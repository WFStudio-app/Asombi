//! Mount — монтирование rootfs с fallback стратегией

use libc::{syscall, SYS_mount, SYS_chroot, SYS_unshare, CLONE_NEWNS};
use std::ffi::CString;
use std::fs;
use std::path::Path;

pub struct MountError(pub String);

impl std::fmt::Display for MountError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

macro_rules! cstr {
    ($s:expr) => { CString::new($s).unwrap() }
}

/// Пытаемся сделать mount. Если EPERM/ENOSYS — не крашимся, возвращаем false
fn try_mount(src: &str, tgt: &str, fs: &str, flags: u64) -> bool {
    unsafe {
        let s = cstr!(src);
        let t = cstr!(tgt);
        let f = cstr!(fs);
        let ret = syscall(SYS_mount, s.as_ptr(), t.as_ptr(), f.as_ptr(), flags, 0usize);
        ret == 0
    }
}

/// Bind mount — src монтируем в tgt
fn try_bind(src: &str, tgt: &str) -> bool {
    unsafe {
        let s = cstr!(src);
        let t = cstr!(tgt);
        // MS_BIND = 4096
        let ret = syscall(SYS_mount, s.as_ptr(), t.as_ptr(),
                         std::ptr::null::<u8>(), 4096usize, 0usize);
        ret == 0
    }
}

/// Создаём папку если не существует — не крашимся если нет прав
fn ensure_dir(path: &str) {
    let _ = fs::create_dir_all(path);
}

pub fn setup_rootfs(rootfs: &str) -> Result<(), MountError> {
    println!("  [mount] Setting up rootfs: {}", rootfs);

    if !Path::new(rootfs).exists() {
        return Err(MountError(format!("Rootfs not found: {}", rootfs)));
    }

    // Пробуем получить новый mount namespace
    unsafe {
        let ret = syscall(SYS_unshare, CLONE_NEWNS);
        if ret == 0 {
            println!("  [mount] ✓ New mount namespace created");
        } else {
            println!("  [mount] ! Running without mount namespace (no root)");
        }
    }

    // Монтируем /proc внутри rootfs
    let proc_path = format!("{}/proc", rootfs);
    ensure_dir(&proc_path);
    if try_mount("proc", &proc_path, "proc", 0) {
        println!("  [mount] ✓ /proc");
    } else {
        // Fallback — bind mount из хоста
        if try_bind("/proc", &proc_path) {
            println!("  [mount] ✓ /proc (bind)");
        } else {
            println!("  [mount] ! /proc unavailable — some tools may not work");
        }
    }

    // /dev
    let dev_path = format!("{}/dev", rootfs);
    ensure_dir(&dev_path);
    if try_bind("/dev", &dev_path) {
        println!("  [mount] ✓ /dev (bind)");
    } else {
        println!("  [mount] ! /dev unavailable");
    }

    // /sys
    let sys_path = format!("{}/sys", rootfs);
    ensure_dir(&sys_path);
    if try_mount("sysfs", &sys_path, "sysfs", 0) {
        println!("  [mount] ✓ /sys");
    } else if try_bind("/sys", &sys_path) {
        println!("  [mount] ✓ /sys (bind)");
    } else {
        println!("  [mount] ! /sys unavailable");
    }

    // /tmp
    let tmp_path = format!("{}/tmp", rootfs);
    ensure_dir(&tmp_path);
    if try_mount("tmpfs", &tmp_path, "tmpfs", 0) {
        println!("  [mount] ✓ /tmp (tmpfs)");
    }

    // Termux home → /termux-home внутри rootfs
    if let Ok(home) = std::env::var("HOME") {
        let th_path = format!("{}/termux-home", rootfs);
        ensure_dir(&th_path);
        if try_bind(&home, &th_path) {
            println!("  [mount] ✓ /termux-home → {}", home);
        }
    }

    // resolv.conf для DNS
    setup_dns(rootfs);

    println!("  [mount] Rootfs ready\n");
    Ok(())
}

fn setup_dns(rootfs: &str) {
    let resolv = format!("{}/etc/resolv.conf", rootfs);
    let _ = ensure_dir(&format!("{}/etc", rootfs));
    if !Path::new(&resolv).exists() {
        let _ = fs::write(&resolv, "nameserver 8.8.8.8\nnameserver 1.1.1.1\n");
    }
}

/// chroot в rootfs
pub fn do_chroot(rootfs: &str) -> Result<(), MountError> {
    unsafe {
        let path = cstr!(rootfs);
        let ret = syscall(SYS_chroot, path.as_ptr());
        if ret != 0 {
            let err = *libc::__errno_location();
            return Err(MountError(format!("chroot failed: errno {}", err)));
        }
        // cd /
        let root = cstr!("/"); libc::chdir(root.as_ptr());
    }
    println!("  [chroot] ✓ Entered rootfs");
    Ok(())
}
