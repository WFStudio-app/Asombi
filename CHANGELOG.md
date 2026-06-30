# Changelog

Versioning system:
- `0.1.01` - mini update (bug fixes, small tweaks)
- `0.1.10` - major update (new features)
- `0.2.00` - new release (significant milestone)

---

## [0.1.10] - 2026-06-30 - Wizzor Go Rewrite + Windows Support

### Added
- Wizzor package manager rewrite started in Go (wizzor-go/)
  - Etap 1: `wiz version`, `wiz help`
  - Etap 2: `wiz search`, `wiz list` (TOML-based index)
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
- PEP8 compliance across all wizzor/core modules

---

## [0.1.00] - 2026-06-28 - Initial Release

### Added
- Alpine Linux 3.19 base via proot (ARM64 + x86_64)
- `os login <instance>` - real Linux session entry point
- `os instances` / `os remove` - instance management
- Wizzor package manager: install, remove, update, search, list, info, repo, clean
- SHA256 checksum verification
- Dependency resolution
- Multi-repository support
- Fastfetch with Asombi logo
- Custom prompt: asombi@asombi-root:~#
- One-command installer (install.sh)

---

(c) WFWorld
