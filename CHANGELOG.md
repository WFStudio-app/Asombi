# Changelog

Versioning system:
- `0.1.01` — mini update (bug fixes, small tweaks)
- `0.1.10` — major update (new features)
- `0.2.00` — new release (significant milestone)

---

## [0.1.00] - 2026-06-28 — Initial Release

### Added
- Alpine Linux 3.19 base via proot (ARM64 + x86_64)
- `os login <instance>` — real Linux session entry point
- `os instances` — list all instances
- `os remove <instance>` — delete instance
- Wizzor package manager with:
  - `wiz install / remove / update / search / list / info`
  - `wiz repo add / remove / list`
  - `wiz clean`
  - SHA256 checksum verification
  - Dependency resolution
  - Multi-repository support
- Fastfetch integration with Asombi logo
- Custom prompt: `asombi@asombi-root:~#`
- One-command installer (`install.sh`)

© WFWorld
