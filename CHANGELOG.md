# Changelog

Versioning system:
- `0.1.01` — mini update (bug fixes, small tweaks)
- `0.1.10` — major update (new features)
- `0.2.00` — new release (significant milestone)

---

## [0.1.01] - 2026-06-29 — Repository & Compatibility Update

### Added
- `.editorconfig` — unified code style across all editors
- `.gitattributes` — normalized line endings (LF) for Windows/Android compatibility
- `CODE_OF_CONDUCT.md`
- `uninstall.sh` — clean uninstaller with data removal prompt
- `PULL_REQUEST_TEMPLATE.md`
- `.github/FUNDING.yml` — sponsor button
- `.github/dependabot.yml` — auto-update GitHub Actions weekly
- Interactive issue templates (`.yml` forms) replacing old `.md` templates
- `docs/faq.md` — frequently asked questions
- `docs/troubleshooting.md` — common issues and fixes
- `docs/packages.md` — guide for creating Wizzor packages
- `docs/architecture.md` — system architecture overview

### Improved
- `install.sh` — architecture check (ARM64/x86_64/armv7), Python 3.8+ version check,
  proot auto-install, cleaner output
- CI split into 3 jobs: Python lint, shellcheck, JSON validation

### Fixed
- PEP8 compliance across all `wizzor/core/` modules (E302, F403, E231)

---

## [0.1.00] - 2026-06-28 — Initial Release

### Added
- Alpine Linux 3.19 base via proot (ARM64 + x86_64)
- `os login <instance>` — real Linux session entry point
- `os instances` / `os remove` — instance management
- Wizzor package manager: `install`, `remove`, `update`, `search`, `list`, `info`, `repo`, `clean`
- SHA256 checksum verification
- Dependency resolution
- Multi-repository support
- Fastfetch with Asombi logo
- Custom prompt: `asombi@asombi-root:~#`
- One-command installer (`install.sh`)

---

© WFWorld
