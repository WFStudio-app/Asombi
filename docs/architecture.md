# Asombi OS — Architecture

## Overview

```
Android Device
└── Termux
    ├── os (Python)          ← Entry point
    │   ├── proot            ← Linux container (no root needed)
    │   │   └── Alpine Linux rootfs
    │   │       ├── /bin /usr /etc  ← Real Linux filesystem
    │   │       ├── /opt/wizzor     ← Wizzor package manager
    │   │       └── /termux-home    ← Bind mount to Termux $HOME
    │   └── ~/.asombi/instances/<name>/rootfs/
    └── wiz (Python)         ← Can also run standalone in Termux
```


## asombi-loader (Rust)

`asombi-loader` is a custom Rust binary that will replace proot as the
container launcher. It is currently in development (`loader/` directory).

```
asombi-loader
├── probe.rs     — detects available kernel syscalls without crashing
├── mount.rs     — sets up rootfs, bind mounts
└── loader.rs    — launches process via execve with full argv
```

**Adaptive strategy** (auto-selected based on kernel capabilities):

| Strategy | Requires | Description |
|----------|----------|-------------|
| `Native` | unshare + mount + chroot | Full namespace isolation |
| `Chroot` | chroot | Root change, no namespace |
| `BindOnly` | nothing | Bind mounts only |

**Current status:** compiled and tested on x86_64 Linux with root.
Not yet integrated into `os login` — proot is still used by default.
Integration planned for v0.2.00.

## Components

### `bin/os`
Entry point. Manages instances, downloads Alpine rootfs on first boot,
launches proot session.

### `bin/wiz`
Wizzor package manager. Works both inside Asombi and standalone in Termux.
Reads sources from `~/.wizzor/sources.list`, stores installed packages in
`~/.wizzor/installed.json`.

### `wizzor/core/`
Modular command handlers — one file per `wiz` subcommand.

### `packages/index.json`
Official package repository index served from GitHub raw.

### Alpine rootfs
Downloaded from `dl-cdn.alpinelinux.org` on first `os login`.
Stored at `~/.asombi/instances/<name>/rootfs/`.

## Data directories (on host)

| Path | Contents |
|------|----------|
| `~/.asombi/instances/<name>/rootfs/` | Alpine Linux filesystem |
| `~/.asombi/instances.json` | Instance registry |
| `~/.wizzor/installed.json` | Installed packages DB |
| `~/.wizzor/sources.list` | Repository list |
| `~/.wizzor/cache/` | Download cache |
| `~/.wizzor/packages/` | Extracted packages |

---

© WFWorld
