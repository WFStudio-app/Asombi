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
  <img src="https://img.shields.io/badge/Version-0.1.11-purple?style=flat-square"/>
</p>

---

## What is Asombi?

Asombi is a real Linux environment that runs on top of Android via Termux — no root required.
It uses `proot` to boot a genuine Alpine Linux rootfs with a custom shell, custom prompt,
and **Wizzor** — its own package manager.

```
asombi@asombi-root:~#
```

---

## Requirements

- **Android** 7.0+ (ARM64 recommended, x86_64 supported)
- **Termux** — [Download from F-Droid](https://f-droid.org/packages/com.termux/) *(not Play Store)*
- Internet connection (~30 MB on first boot)

---

## Installation

```bash
# 1. Update Termux
pkg update && pkg upgrade -y

# 2. Install dependencies
pkg install git python proot -y

# 3. One-command install
curl -sL https://raw.githubusercontent.com/WFStudio-app/Asombi/main/install.sh | bash
```

Or manual:
```bash
git clone https://github.com/WFStudio-app/Asombi.git
cd Asombi && bash install.sh
```

---

## First Boot

```bash
os login asombi-1
```

On first boot Asombi downloads Alpine Linux, sets up the environment,
installs Wizzor, and drops you into a live shell.

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

apk add <package>       # Alpine native packages (also available)
```

---

## Versioning

| Version | Type | Description |
|---------|------|-------------|
| `0.1.01` | Mini update | Bug fixes, small tweaks |
| `0.1.10` | Major update | New features |
| `0.2.00` | New release | Significant milestone |

Current version: **0.1.11**

---

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/faq.md](docs/faq.md) | Frequently asked questions |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues and fixes |
| [docs/wizzor.md](docs/wizzor.md) | Wizzor command reference |
| [docs/packages.md](docs/packages.md) | Creating and publishing packages |
| [docs/instances.md](docs/instances.md) | Managing instances |
| [docs/architecture.md](docs/architecture.md) | System architecture |

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
├── .github/             ← CI, issue templates, PR template
├── install.sh           ← Installer
├── uninstall.sh         ← Uninstaller
├── LICENSE              ← MIT
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── SECURITY.md
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## Security

See [SECURITY.md](SECURITY.md)

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

---

## License

MIT License — see [LICENSE](LICENSE)

© WFWorld
