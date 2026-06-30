mod probe;
mod mount;
mod loader;

use std::process;

fn main() {
    println!("\n  Asombi Loader v0.1.0");
    println!("  Probing Android kernel capabilities...\n");

    let caps = probe::KernelCapabilities::detect();
    caps.print_report();

    let rootfs = std::env::args().nth(1).unwrap_or_else(|| {
        eprintln!("  [!] Usage: asombi-loader <rootfs_path> [cmd]");
        process::exit(1);
    });

    let rest_args: Vec<String> = std::env::args().skip(2).collect();
    let cmd_args = if rest_args.is_empty() {
        vec!["/bin/sh".to_string()]
    } else {
        rest_args
    };

    match loader::launch(&rootfs, &cmd_args, &caps) {
        Ok(_) => {},
        Err(e) => {
            eprintln!("  [!] Launch failed: {}", e);
            process::exit(1);
        }
    }
}
