//! Probe — определяем что поддерживает Android kernel
//! Пробуем каждый syscall и запоминаем результат без краша

use libc::{syscall, SYS_mount, SYS_unshare,
           SYS_chroot, SYS_pivot_root, CLONE_NEWNS, EINVAL, EPERM, ENOSYS};
use std::ffi::CString;

/// Что умеет этот Android kernel
#[derive(Debug, Clone)]
pub struct KernelCapabilities {
    pub has_mount:      bool, // SYS_mount работает
    pub has_chroot:     bool, // SYS_chroot доступен
    pub has_unshare:    bool, // mount namespace isolation
    pub has_pivot_root: bool, // полная смена root
    pub has_clone_ns:   bool, // CLONE_NEWNS (новый namespace)
    pub android_api:    u32,  // версия Android API
    pub arch:           &'static str,
}

impl KernelCapabilities {
    /// Пробуем каждый syscall — не крашимся, просто запоминаем
    pub fn detect() -> Self {
        KernelCapabilities {
            has_mount:      Self::probe_mount(),
            has_chroot:     Self::probe_chroot(),
            has_unshare:    Self::probe_unshare(),
            has_pivot_root: Self::probe_pivot_root(),
            has_clone_ns:   Self::probe_clone_ns(),
            android_api:    Self::detect_android_api(),
            arch:           Self::detect_arch(),
        }
    }

    /// Пробуем SYS_mount с заведомо неверными аргументами
    /// EPERM = есть но нет прав, ENOSYS = нет совсем, EINVAL = есть
    fn probe_mount() -> bool {
        unsafe {
            let src = CString::new("none").unwrap();
            let tgt = CString::new("/proc").unwrap();
            let fs  = CString::new("proc").unwrap();
            let ret = syscall(SYS_mount,
                src.as_ptr(), tgt.as_ptr(), fs.as_ptr(), 0usize, 0usize);
            // ENOSYS = точно нет, остальное = есть (включая EPERM)
            let err = *libc::__errno_location();
            ret == 0 || err != ENOSYS as i32
        }
    }

    fn probe_chroot() -> bool {
        unsafe {
            let path = CString::new("/nonexistent_asombi_probe").unwrap();
            syscall(SYS_chroot, path.as_ptr());
            let err = *libc::__errno_location();
            err != ENOSYS as i32
        }
    }

    fn probe_unshare() -> bool {
        unsafe {
            // Пробуем unshare с 0 — минимальный эффект
            let ret = syscall(SYS_unshare, 0i32);
            let err = *libc::__errno_location();
            ret == 0 || (err != ENOSYS as i32 && err != EINVAL as i32)
        }
    }

    fn probe_pivot_root() -> bool {
        unsafe {
            let new = CString::new("/").unwrap();
            let old = CString::new("/").unwrap();
            syscall(SYS_pivot_root, new.as_ptr(), old.as_ptr());
            let err = *libc::__errno_location();
            err != ENOSYS as i32
        }
    }

    fn probe_clone_ns() -> bool {
        unsafe {
            // Пробуем unshare(CLONE_NEWNS)
            let ret = syscall(SYS_unshare, CLONE_NEWNS);
            let err = *libc::__errno_location();
            ret == 0 || err == EPERM as i32 // EPERM = есть но нет прав
        }
    }

    fn detect_android_api() -> u32 {
        // Читаем из /proc/version или system properties
        if let Ok(v) = std::fs::read_to_string("/proc/version") {
            if v.contains("android") || v.contains("Android") {
                // Пробуем найти API level
                if let Ok(p) = std::fs::read_to_string(
                    "/system/build.prop"
                ) {
                    for line in p.lines() {
                        if line.starts_with("ro.build.version.sdk=") {
                            if let Ok(n) = line[21..].parse::<u32>() {
                                return n;
                            }
                        }
                    }
                }
                return 0; // Android но версию не нашли
            }
        }
        0
    }

    fn detect_arch() -> &'static str {
        #[cfg(target_arch = "aarch64")] { "aarch64" }
        #[cfg(target_arch = "x86_64")]  { "x86_64"  }
        #[cfg(target_arch = "arm")]      { "armv7"   }
        #[cfg(not(any(
            target_arch = "aarch64",
            target_arch = "x86_64",
            target_arch = "arm"
        )))]
        { "unknown" }
    }

    pub fn print_report(&self) {
        println!("\n  ── Kernel Capabilities ──────────────────");
        println!("  arch:        {}", self.arch);
        if self.android_api > 0 {
            println!("  android api: {}", self.android_api);
        }
        Self::print_cap("mount",      self.has_mount);
        Self::print_cap("chroot",     self.has_chroot);
        Self::print_cap("unshare",    self.has_unshare);
        Self::print_cap("pivot_root", self.has_pivot_root);
        Self::print_cap("clone_ns",   self.has_clone_ns);
        println!("  ─────────────────────────────────────────\n");
    }

    fn print_cap(name: &str, val: bool) {
        let (sym, col) = if val {
            ("✓", "\x1b[92m")
        } else {
            ("✗", "\x1b[91m")
        };
        println!("  {col}{sym}\x1b[0m  {name}");
    }

    /// Выбираем стратегию запуска исходя из возможностей
    pub fn strategy(&self) -> Strategy {
        if self.has_unshare && self.has_mount && self.has_chroot {
            Strategy::Native
        } else if self.has_chroot {
            Strategy::Chroot
        } else {
            Strategy::BindOnly
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub enum Strategy {
    /// Полная изоляция: unshare + mount + chroot
    Native,
    /// Только chroot без namespace
    Chroot,
    /// Минимальный режим: только bind mounts, без chroot
    BindOnly,
}

impl std::fmt::Display for Strategy {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            Strategy::Native   => write!(f, "Native (full isolation)"),
            Strategy::Chroot   => write!(f, "Chroot (no namespace)"),
            Strategy::BindOnly => write!(f, "BindOnly (minimal)"),
        }
    }
}
