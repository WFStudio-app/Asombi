use libc::{syscall, SYS_unshare, SYS_mount, SYS_pivot_root, SYS_chdir, CLONE_NEWNS, CLONE_NEWUSER, CLONE_NEWUTS, CLONE_NEWIPC};
use std::ffi::CString;
use std::fs;
use std::path::Path;

pub struct NsError(pub String);

impl std::fmt::Display for NsError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

fn cstr(s: &str) -> CString {
    CString::new(s).unwrap()
}

fn errno() -> i32 {
    unsafe { *libc::__errno_location() }
}

fn try_unshare(flag: libc::c_int) -> bool {
    unsafe { syscall(SYS_unshare, flag) == 0 }
}

pub fn setup_user_namespace() -> Result<(), NsError> {
    let uid = unsafe { libc::getuid() };
    let gid = unsafe { libc::getgid() };

    if !try_unshare(CLONE_NEWUSER) {
        return Err(NsError(format!(
            "CLONE_NEWUSER failed: errno {} — user namespaces not available on this kernel",
            errno()
        )));
    }

    write_uid_gid_map(uid, gid)?;

    let _ = try_unshare(CLONE_NEWNS);
    let _ = try_unshare(CLONE_NEWUTS);
    let _ = try_unshare(CLONE_NEWIPC);

    Ok(())
}

fn write_uid_gid_map(uid: u32, gid: u32) -> Result<(), NsError> {
    fs::write("/proc/self/uid_map", format!("0 {} 1\n", uid))
        .map_err(|e| NsError(format!("uid_map write failed: {}", e)))?;

    fs::write("/proc/self/setgroups", "deny")
        .map_err(|e| NsError(format!("setgroups write failed: {}", e)))?;

    fs::write("/proc/self/gid_map", format!("0 {} 1\n", gid))
        .map_err(|e| NsError(format!("gid_map write failed: {}", e)))?;

    Ok(())
}

fn try_mount(src: &str, tgt: &str, fstype: &str, flags: u64) -> bool {
    unsafe {
        let s = cstr(src);
        let t = cstr(tgt);
        let f = cstr(fstype);
        syscall(SYS_mount, s.as_ptr(), t.as_ptr(), f.as_ptr(), flags, 0usize) == 0
    }
}

fn try_bind(src: &str, tgt: &str) -> bool {
    unsafe {
        let s = cstr(src);
        let t = cstr(tgt);
        syscall(SYS_mount, s.as_ptr(), t.as_ptr(),
            std::ptr::null::<u8>(), 4096usize, 0usize) == 0
    }
}

fn ensure_dir(path: &str) {
    let _ = fs::create_dir_all(path);
}

pub fn setup_rootfs(rootfs: &str) -> Result<(), NsError> {
    if !Path::new(rootfs).exists() {
        return Err(NsError(format!("rootfs not found: {}", rootfs)));
    }

    let mounts = [
        (format!("{}/proc", rootfs), "proc",  "proc",  false),
        (format!("{}/dev",  rootfs), "/dev",   "",     true),
        (format!("{}/sys",  rootfs), "sysfs", "sysfs", false),
        (format!("{}/tmp",  rootfs), "tmpfs", "tmpfs", false),
    ];

    for (tgt, src, fstype, is_bind) in &mounts {
        ensure_dir(tgt);
        if *is_bind {
            if !try_bind(src, tgt) {
                eprintln!("  [!] bind {} failed", src);
            }
        } else {
            if !try_mount(src, tgt, fstype, 0) {
                let _ = try_bind(src, tgt);
            }
        }
    }

    if let Ok(home) = std::env::var("HOME") {
        let th = format!("{}/termux-home", rootfs);
        ensure_dir(&th);
        try_bind(&home, &th);
    }

    let resolv = format!("{}/etc/resolv.conf", rootfs);
    if !Path::new(&resolv).exists() {
        ensure_dir(&format!("{}/etc", rootfs));
        let _ = fs::write(&resolv, "nameserver 8.8.8.8\nnameserver 1.1.1.1\n");
    }

    Ok(())
}

pub fn do_pivot_root(rootfs: &str) -> Result<(), NsError> {
    let put_old = format!("{}/mnt", rootfs);
    ensure_dir(&put_old);

    unsafe {
        let new = cstr(rootfs);
        let old = cstr(&put_old);

        if syscall(SYS_pivot_root, new.as_ptr(), old.as_ptr()) == 0 {
            syscall(SYS_chdir, cstr("/").as_ptr());
            let mnt = cstr("/mnt");
            syscall(SYS_mount, std::ptr::null::<u8>(), mnt.as_ptr(),
                std::ptr::null::<u8>(), libc::MNT_DETACH as u64, 0usize);
            let _ = fs::remove_dir("/mnt");
            return Ok(());
        }
    }

    do_chroot(rootfs)
}

pub fn do_chroot(rootfs: &str) -> Result<(), NsError> {
    unsafe {
        let p = cstr(rootfs);
        if libc::chroot(p.as_ptr()) != 0 {
            return Err(NsError(format!("chroot failed: errno {}", errno())));
        }
        let root = cstr("/");
        libc::chdir(root.as_ptr());
    }
    Ok(())
}
