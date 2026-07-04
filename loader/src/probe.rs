use libc::{syscall, SYS_unshare, SYS_mount, SYS_chroot, SYS_pivot_root, CLONE_NEWNS, CLONE_NEWUSER, CLONE_NEWPID, CLONE_NEWUTS, CLONE_NEWIPC};
use std::ffi::CString;

#[derive(Debug, Clone)]
pub struct KernelCapabilities {
    pub has_user_ns:  bool,
    pub has_mount_ns: bool,
    pub has_pid_ns:   bool,
    pub has_uts_ns:   bool,
    pub has_ipc_ns:   bool,
    pub has_mount:    bool,
    pub has_chroot:   bool,
    pub has_pivot:    bool,
    pub android_api:  u32,
    pub arch:         &'static str,
}

impl KernelCapabilities {
    pub fn detect() -> Self {
        KernelCapabilities {
            has_user_ns:  Self::probe_user_ns(),
            has_mount_ns: Self::probe_ns(CLONE_NEWNS),
            has_pid_ns:   Self::probe_ns(CLONE_NEWPID),
            has_uts_ns:   Self::probe_ns(CLONE_NEWUTS),
            has_ipc_ns:   Self::probe_ns(CLONE_NEWIPC),
            has_mount:    Self::probe_mount(),
            has_chroot:   Self::probe_chroot(),
            has_pivot:    Self::probe_pivot(),
            android_api:  Self::detect_android_api(),
            arch:         Self::detect_arch(),
        }
    }

    fn probe_user_ns() -> bool {
        unsafe {
            let ret = syscall(SYS_unshare, CLONE_NEWUSER);
            let e = *libc::__errno_location();
            ret == 0 || e == libc::EPERM as i32
        }
    }

    fn probe_ns(flag: libc::c_int) -> bool {
        unsafe {
            let ret = syscall(SYS_unshare, flag);
            let e = *libc::__errno_location();
            ret == 0 || (e != libc::ENOSYS as i32 && e != libc::EINVAL as i32)
        }
    }

    fn probe_mount() -> bool {
        unsafe {
            let s = CString::new("none").unwrap();
            let t = CString::new("/proc").unwrap();
            let f = CString::new("proc").unwrap();
            syscall(SYS_mount, s.as_ptr(), t.as_ptr(), f.as_ptr(), 0usize, 0usize);
            *libc::__errno_location() != libc::ENOSYS as i32
        }
    }

    fn probe_chroot() -> bool {
        unsafe {
            let p = CString::new("/nonexistent_asombi_probe").unwrap();
            syscall(SYS_chroot, p.as_ptr());
            *libc::__errno_location() != libc::ENOSYS as i32
        }
    }

    fn probe_pivot() -> bool {
        unsafe {
            let p = CString::new("/").unwrap();
            syscall(SYS_pivot_root, p.as_ptr(), p.as_ptr());
            *libc::__errno_location() != libc::ENOSYS as i32
        }
    }

    fn detect_android_api() -> u32 {
        if let Ok(p) = std::fs::read_to_string("/system/build.prop") {
            for line in p.lines() {
                if line.starts_with("ro.build.version.sdk=") {
                    if let Ok(n) = line[21..].parse::<u32>() {
                        return n;
                    }
                }
            }
        }
        0
    }

    fn detect_arch() -> &'static str {
        #[cfg(target_arch = "aarch64")] { "aarch64" }
        #[cfg(target_arch = "x86_64")]  { "x86_64"  }
        #[cfg(target_arch = "arm")]     { "armv7"   }
        #[cfg(not(any(
            target_arch = "aarch64",
            target_arch = "x86_64",
            target_arch = "arm"
        )))] { "unknown" }
    }

    pub fn strategy(&self) -> Strategy {
        if self.has_user_ns && self.has_mount_ns {
            Strategy::UserNamespace
        } else if self.has_mount && self.has_chroot {
            Strategy::MountChroot
        } else if self.has_chroot {
            Strategy::ChrootOnly
        } else {
            Strategy::BindOnly
        }
    }

    pub fn print_report(&self) {
        println!("\n  Kernel Capabilities");
        println!("  arch: {}  android_api: {}", self.arch, self.android_api);
        Self::cap("user_namespace",  self.has_user_ns);
        Self::cap("mount_namespace", self.has_mount_ns);
        Self::cap("pid_namespace",   self.has_pid_ns);
        Self::cap("uts_namespace",   self.has_uts_ns);
        Self::cap("ipc_namespace",   self.has_ipc_ns);
        Self::cap("mount",           self.has_mount);
        Self::cap("chroot",          self.has_chroot);
        Self::cap("pivot_root",      self.has_pivot);
        println!("  strategy: {}\n", self.strategy());
    }

    fn cap(name: &str, val: bool) {
        let sym = if val { "\x1b[92m✓\x1b[0m" } else { "\x1b[91m✗\x1b[0m" };
        println!("  {}  {}", sym, name);
    }
}

#[derive(Debug, Clone, PartialEq)]
pub enum Strategy {
    UserNamespace,
    MountChroot,
    ChrootOnly,
    BindOnly,
}

impl std::fmt::Display for Strategy {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            Strategy::UserNamespace => write!(f, "UserNamespace (fastest, no root needed)"),
            Strategy::MountChroot   => write!(f, "MountChroot (root required)"),
            Strategy::ChrootOnly    => write!(f, "ChrootOnly (root required)"),
            Strategy::BindOnly      => write!(f, "BindOnly (minimal)"),
        }
    }
}
