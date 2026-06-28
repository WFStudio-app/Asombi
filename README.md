<h1 align="center">ASOMBI OS</h1>
<p align="center">
  A real Linux operating environment for Android · Built on Alpine Linux · ARM64 native
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Base-Alpine%20Linux%203.19-blue?style=flat-square&logo=alpinelinux"/>
  <img src="https://img.shields.io/badge/Arch-ARM64%20%2F%20x86__64-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/Package%20Manager-Wizzor-cyan?style=flat-square"/>
  <img src="https://img.shields.io/badge/Platform-Termux%20%2F%20Android-orange?style=flat-square&logo=android"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square"/>
</p>

---

## What is Asombi?

Asombi is a real Linux environment that runs on top of Android via Termux — no root required on your device. It uses `proot` to boot a genuine Alpine Linux rootfs, with a custom shell, custom prompt, and **Wizzor** — its own package manager.

When you log in you get a real shell:
```
asombi@asombi-root:~#
```
With real `/bin`, `/etc`, `/usr`, full Alpine package repos (`apk`) and Wizzor (`wiz`) side by side.

---

## Requirements

- **Android** device (ARM64 recommended, x86_64 also supported)
- **Termux** — [Download from F-Droid](https://f-droid.org/packages/com.termux/)
- Internet connection for first setup (~30 MB)

---

## Installation

### Step 1 — Install Termux

Download Termux from F-Droid (not Play Store):
```
https://f-droid.org/packages/com.termux/
```

### Step 2 — Update packages

```bash
pkg update && pkg upgrade -y
```

### Step 3 — Install dependencies

```bash
pkg install git python -y
```

### Step 4 — Clone Asombi

```bash
git clone https://github.com/WFStudio-app/Asombi.git
cd Asombi
```

### Step 5 — Run installer

```bash
bash install.sh
```

---

## First Boot

```bash
os login asombi-1
```

On first boot Asombi will download Alpine Linux, configure the environment, install Wizzor, and drop you into a live shell.

---

## Usage

### From Termux

```bash
os login <name>         # Start or create an instance
os instances            # List all instances
os remove <name>        # Delete an instance
os version              # Show version
```

### Inside Asombi

```bash
wiz install <package>   # Install a package
wiz remove  <package>   # Remove a package
wiz update              # Update all packages
wiz search  <query>     # Search packages
wiz list                # List installed packages
wiz info    <package>   # Show package info
wiz repo add <url>      # Add a repository
wiz clean               # Clear cache

apk add <package>       # Alpine native package manager
```

---

## Wizzor Repository Format

```json
{
  "repo": "My Repo",
  "maintainer": "you",
  "packages": {
    "my-tool": {
      "version": "1.0.0",
      "description": "What it does",
      "url": "https://example.com/my-tool.tar.gz",
      "sha256": "abc123...",
      "size": "200 KB",
      "depends": [],
      "license": "MIT"
    }
  }
}
```

---

## Project Structure

```
Asombi/
├── bin/
│   ├── os               ← Entry point
│   └── wiz              ← Package manager
├── wizzor/core/         ← Wizzor modules
├── packages/index.json  ← Official package index
├── assets/              ← Logo, fastfetch config
├── docs/                ← Documentation
├── .github/             ← Issue templates, workflows
├── LICENSE              ← MIT License
├── CONTRIBUTING.md      ← Contribution guide
├── CHANGELOG.md         ← Version history
├── SECURITY.md          ← Security policy
└── install.sh           ← One-command installer
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## Security

See [SECURITY.md](SECURITY.md)

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

---

## License

MIT License — see [LICENSE](LICENSE)

© WFWorld
