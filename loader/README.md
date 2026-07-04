# asombi-loader

Custom container launcher for Asombi OS written in Rust.
Replaces proot with direct Linux kernel interfaces.

## Why not proot

proot intercepts every syscall in userspace — slow, unreliable, drains battery.
asombi-loader talks to the kernel directly with no intermediary layer.

## Strategy (auto-selected)

| Strategy | How | Requires |
|----------|-----|----------|
| UserNamespace | CLONE_NEWUSER + pivot_root | Android 9+, kernel config |
| MountChroot | mount + chroot | root |
| ChrootOnly | chroot only | root |
| BindOnly | bind mounts | nothing |

UserNamespace is the primary target: no root needed, full isolation,
native kernel speed. The loader probes the kernel and falls back automatically.

## Build

```bash
cargo build --release

CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER=aarch64-linux-android-clang \
    cargo build --release --target aarch64-linux-android
```

## Usage

```bash
asombi-loader <rootfs> [command] [args...]
asombi-loader ~/.asombi/instances/asombi-1/rootfs /bin/sh -l
```

## Files

```
src/main.rs       entry point
src/probe.rs      kernel capability detection
src/namespace.rs  user namespaces, mounts, pivot_root, chroot
src/loader.rs     strategy selection and execve
```

(c) WFWorld - MIT License
