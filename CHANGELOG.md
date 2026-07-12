## [0.2.00-beta] - 2026-07-13 — First Beta Release

### Highlights
- First public beta of Asombi OS
- Wizzor renamed to **Truck** (`trk` command)
- Boot layer rewritten in **C** (was Python) — faster startup
- Custom **Rust loader** replacing proot (asombi-loader)
- New ASCII logo

### Added
- `bin/os` rewritten in C — zero Python dependency for boot
- `asombi-loader` (Rust) — direct Linux namespaces, no proot overhead
- BIOS system (.bios command) — network, system, data, memory settings
- `os delete` command — remove instances
- Pre-flight checks before every login (network, mirror, deps)
- Rootfs integrity check with auto-repair
- New download progress bar: `[045%] Downloading packages... 00 h 02 min 13 sec`
- macOS support via Lima VM (`install-macos.sh`)
- New ASCII logo (small + large variants)
- shellcheck, nano, wget, busybox added to package index
- Centralized path system (`truck/core/paths.py`)
- `os delete --all`, `os delete --full` commands

### Fixed
- proot `--link2symlink -0` flags — fixes Alpine symlinks
- `check_rootfs` uses `lexists` — detects Alpine busybox symlinks correctly
- Rootfs no longer deleted on integrity check failure — repair attempted
- `bin/trk` IndentationError fixed
- Python3 auto-installed via apk on first boot
- All Wizzor/wiz references renamed to Truck/trk
- `uninstall.sh` now removes correct commands (os + trk)
- `install.sh` — single python3 subprocess call (was 3)
- `install.sh` — disk space check before download
- `install.sh` — git clone with diagnostics
- TOML parser quoting bug fixed
- Duplicate imports in `bin/os` removed

### Stack
- Boot: **C**
- Package manager: **Python** (Go rewrite in progress)
- Loader: **Rust**
- Package index format: **TOML**

---

# Changelog

Versioning system:
- `0.1.01` - mini update (bug fixes, small tweaks)
- `0.1.10` - major update (new features)
- `0.2.00` - new release (significant milestone)

---

## [0.1.11] - 2026-07-03 — Bug Fix Release

### Fixed
- **Bug #1** `install.sh` — идемпотентный установщик: если запущен из уже клонированной папки — не клонирует заново, использует текущую
- **Bug #1** `README.md` — убран двойной `git clone`; установка через один `curl | bash`
- **Bug #2** `docs/troubleshooting.md` — исправлена ссылка `index.json` → `index.toml`
- **Bug #3** `install.sh` — предупреждение про Android 12+ Phantom Process Killer при установке
- **Bug #4** `docs/truck.md` — добавлена таблица статуса Python/Go миграции
- **Bug #5** `docs/architecture.md` — задокументирован `asombi-loader` и план интеграции
- **Bug #6** `install.sh` — симлинки не перезаписывают существующие файлы которые не принадлежат Asombi
- **Bug #7** `README.md` — бейдж версии обновлён с `0.1.01` до `0.1.10`
- **Bug #8** `install.sh` — Python версия проверяется одним subprocess вызовом вместо трёх
- `bin/trk` — `realpath()` вместо `abspath()` для корректной работы через симлинк
- `bin/os` — `/bin/sh -l` вместо `--login` для правильной загрузки `/etc/profile` в Alpine ash
- `truck/core/` — централизованное дерево путей через `paths.py`, все файлы Asombi строго в `~/.asombi/`
- `truck/core/install.py` — защита от path traversal в tar/zip архивах
- `truck/core/repo.py` — валидация TOML формата при `trk repo add`
- Все `truck/core/` файлы — явные импорты вместо `from utils import *`

### Added
- `truck/core/paths.py` — централизованный модуль путей файловой системы
- `bin/os delete` — команда удаления инстансов (`delete <name>`, `--all`, `--full`)
- `packages/index.toml` — 8 реальных пакетов с верифицированными SHA256

---

## [0.1.10] - 2026-06-30 - Truck Go Rewrite + Windows Support

### Added
- Truck package manager rewrite started in Go (truck-go/)
  - Etap 1: `trk version`, `trk help`
  - Etap 2: `trk search`, `trk list` (TOML-based index)
- Custom TOML parser (zero dependencies) replacing JSON for package index
- `packages/index.toml` - official index migrated from JSON to TOML
- Cross-platform support: Linux (amd64/arm64), Windows (amd64), macOS (amd64/arm64)
- Windows ANSI color support (Windows Terminal / Windows 10+ cmd.exe)
- Cross-platform home directory detection (USERPROFILE on Windows, HOME on Unix)
- CI workflow building binaries for all 5 platform/arch combinations automatically
- `asombi-loader` - Rust-based custom loader replacing proot
  - Kernel capability probing (mount, chroot, unshare, pivot_root)
  - Graceful fallback strategy: Native > Chroot > BindOnly
  - Does not crash on unsupported syscalls

### Changed
- Package index format: JSON to TOML (more readable, supports comments)

---

## [0.1.01] - 2026-06-29 - Repository & Compatibility Update

### Added
- `.editorconfig`, `.gitattributes` - line ending normalization
- `CODE_OF_CONDUCT.md`
- `uninstall.sh` - clean uninstaller
- Interactive issue templates (yml forms)
- `PULL_REQUEST_TEMPLATE.md`
- `FUNDING.yml`, `dependabot.yml`
- `docs/faq.md`, `docs/troubleshooting.md`, `docs/packages.md`, `docs/architecture.md`

### Improved
- `install.sh` - architecture check, Python 3.8+ check, proot auto-install
- CI split into 3 jobs: Python lint, shellcheck, JSON validation

### Fixed
- PEP8 compliance across all truck/core modules

---

## [0.1.00] - 2026-06-28 - Initial Release

### Added
- Alpine Linux 3.19 base via proot (ARM64 + x86_64)
- `os login <instance>` - real Linux session entry point
- `os instances` / `os remove` - instance management
- Truck package manager: install, remove, update, search, list, info, repo, clean
- SHA256 checksum verification
- Dependency resolution
- Multi-repository support
- Fastfetch with Asombi logo
- Custom prompt: asombi@asombi-root:~#
- One-command installer (install.sh)

---

(c) WFWorld
