//! Loader — запускаем процесс внутри rootfs

use crate::probe::{KernelCapabilities, Strategy};
use crate::mount;
use std::ffi::CString;

pub fn launch(rootfs: &str, cmd_args: &[String], caps: &KernelCapabilities) -> Result<(), String> {
    let strategy = caps.strategy();
    println!("  [loader] Strategy: {}", strategy);

    mount::setup_rootfs(rootfs).map_err(|e| e.to_string())?;

    match strategy {
        Strategy::Native | Strategy::Chroot => {
            mount::do_chroot(rootfs).map_err(|e| e.to_string())?;
        }
        Strategy::BindOnly => {
            println!("  [loader] ! chroot unavailable — using bind-only mode");
            println!("  [loader] ! Some filesystem paths may differ");
        }
    }

    exec(cmd_args)
}

fn exec(cmd_args: &[String]) -> Result<(), String> {
    println!("  [loader] Executing: {}\n", cmd_args.join(" "));

    let path = CString::new(cmd_args[0].as_str()).map_err(|e| e.to_string())?;

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

    // Все аргументы команды (argv[0] = путь, остальное = аргументы)
    let arg_cstrings: Vec<CString> = cmd_args.iter()
        .map(|s| CString::new(s.as_str()).unwrap())
        .collect();
    let argv_ptrs: Vec<*const libc::c_char> = arg_cstrings.iter()
        .map(|s| s.as_ptr())
        .chain(std::iter::once(std::ptr::null()))
        .collect();

    unsafe {
        libc::execve(path.as_ptr(), argv_ptrs.as_ptr(), env_ptrs.as_ptr());
        let err = *libc::__errno_location();
        Err(format!("execve failed: errno {}", err))
    }
}
