mod probe;
mod namespace;
mod loader;

use std::process;

fn main() {
    let args: Vec<String> = std::env::args().collect();

    if args.len() < 2 {
        eprintln!("  Usage: asombi-loader <rootfs> [cmd] [args...]");
        process::exit(1);
    }

    let caps = probe::KernelCapabilities::detect();
    caps.print_report();

    let rootfs = &args[1];
    let cmd_args = if args.len() > 2 {
        args[2..].to_vec()
    } else {
        vec!["/bin/sh".to_string(), "-l".to_string()]
    };

    match loader::launch(rootfs, &cmd_args, &caps) {
        Ok(_) => {}
        Err(e) => {
            eprintln!("  [!] Launch failed: {}", e);
            process::exit(1);
        }
    }
}
