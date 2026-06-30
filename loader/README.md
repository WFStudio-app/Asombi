# asombi-loader

Custom loader for Asombi OS written in Rust.

Replaces proot with a smarter layer that:
- Probes the Android kernel for available syscalls
- Uses the best available strategy (Native > Chroot > BindOnly)
- Does not crash on unsupported syscalls — graceful fallback
- Direct syscalls where possible, no libc wrapper overhead

## Testing status (honest)

**Tested for real** on a Linux container with full root (x86_64):
- mount /proc, /dev (bind), /sys, /tmp (tmpfs) — confirmed working
- unshare(CLONE_NEWNS) — confirmed working
- chroot into rootfs — confirmed working
- execve with arguments inside chroot — confirmed working (`echo` ran correctly inside isolated rootfs)

**NOT yet tested:**
- On real Android/Termux without root (this is the actual target environment —
  capability detection code exists but has not been verified on-device)
- Against a real Alpine Linux rootfs (network restrictions during development
  prevented downloading it — only tested against a minimal hand-built rootfs)
- ARM64 cross-compiled binary has not been run, only compiled

## Build

```bash
cargo build --release
GOOS=linux GOARCH=arm64 # N/A — this is Rust, use:
cargo build --release --target aarch64-linux-android
```

## Usage

```bash
asombi-loader <rootfs_path> <command> [args...]
asombi-loader ~/.asombi/instances/asombi-1/rootfs /bin/sh
```

## Strategies

| Strategy | Requires | Description |
|----------|----------|--------------|
| `Native` | unshare + mount + chroot | Full namespace isolation |
| `Chroot` | chroot | Root change, no namespace |
| `BindOnly` | nothing | Bind mounts only, minimal |

## Architecture

```
main.rs      - Entry point, arg parsing
probe.rs     - Kernel capability detection (syscall probing)
mount.rs     - Rootfs setup, bind mounts, chroot
loader.rs    - Launch strategy + execve with full argv
```

(c) WFWorld - MIT License
