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

    let cmd = std::env::args().nth(2)
        .unwrap_or_else(|| "/bin/sh".to_string());

    match loader::launch(&rootfs, &cmd, &caps) {
        Ok(_) => {},
        Err(e) => {
            eprintln!("  [!] Launch failed: {}", e);
            process::exit(1);
        }
    }
}
