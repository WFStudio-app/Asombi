# asombi-loader

Custom loader for Asombi OS written in Rust.

Replaces proot with a smarter layer that:
- Probes the Android kernel for available syscalls
- Uses the best available strategy (Native > Chroot > BindOnly)
- Does not crash on unsupported syscalls — graceful fallback
- Direct syscalls where possible, no libc wrapper overhead

## Build

```bash
# For host (testing)
cargo build --release

# For ARM64 (Android/Termux)
cargo build --release --target aarch64-linux-android
```

## Usage

```bash
asombi-loader <rootfs_path> [command]
asombi-loader ~/.asombi/instances/asombi-1/rootfs /bin/sh
```

## Strategies

| Strategy | Requires | Description |
|----------|----------|-------------|
| `Native` | unshare + mount + chroot | Full namespace isolation |
| `Chroot` | chroot | Root change, no namespace |
| `BindOnly` | nothing | Bind mounts only, minimal |

The loader auto-detects which strategy is available on your kernel.

## Architecture

```
main.rs      - Entry point, arg parsing
probe.rs     - Kernel capability detection (syscall probing)
mount.rs     - Rootfs setup, bind mounts, chroot
loader.rs    - Launch strategy + execve
```

(c) WFWorld - MIT License
