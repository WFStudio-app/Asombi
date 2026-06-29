//! Loader — запускаем процесс внутри rootfs

use crate::probe::{KernelCapabilities, Strategy};
use crate::mount;
use std::ffi::CString;

pub fn launch(rootfs: &str, cmd: &str, caps: &KernelCapabilities) -> Result<(), String> {
    let strategy = caps.strategy();
    println!("  [loader] Strategy: {}", strategy);

    // Монтируем rootfs
    mount::setup_rootfs(rootfs).map_err(|e| e.to_string())?;

    match strategy {
        Strategy::Native | Strategy::Chroot => {
            // Делаем chroot
            mount::do_chroot(rootfs).map_err(|e| e.to_string())?;
        }
        Strategy::BindOnly => {
            println!("  [loader] ! chroot unavailable — using bind-only mode");
            println!("  [loader] ! Some filesystem paths may differ");
        }
    }

    // Запускаем команду через execv
    exec(cmd)
}

fn exec(cmd: &str) -> Result<(), String> {
    println!("  [loader] Executing: {}\n", cmd);

    let path = CString::new(cmd).map_err(|e| e.to_string())?;

    // Базовые переменные окружения внутри Asombi
    let env_vars = [
        "TERM=xterm-256color",
        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "SHELL=/bin/sh",
        "USER=root",
        "HOME=/root",
        "ASOMBI=1",
    ];

    let env_cstrings: Vec<CString> = env_vars.iter()
        .map(|s| CString::new(*s).unwrap())
        .collect();
    let env_ptrs: Vec<*const libc::c_char> = env_cstrings.iter()
        .map(|s| s.as_ptr())
        .chain(std::iter::once(std::ptr::null()))
        .collect();

    let argv = [path.as_ptr(), std::ptr::null()];

    unsafe {
        libc::execve(path.as_ptr(), argv.as_ptr(), env_ptrs.as_ptr());
        // Если дошли сюда — execve не сработал
        let err = *libc::__errno_location();
        Err(format!("execve failed: errno {}", err))
    }
}
