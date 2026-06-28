# Changelog

All notable changes to Asombi OS are documented here.

## [0.1.0] - 2026-06-28

### Added
- Initial release of Asombi OS
- Alpine Linux 3.19 base via proot (ARM64 + x86_64)
- `os login <instance>` — real Linux session entry point
- `os instances` — list instances
- `os remove` — delete instances
- Wizzor package manager (`wiz`) with:
  - `install`, `remove`, `update`, `search`, `list`, `info`
  - `repo add/remove/list`
  - `clean`
  - SHA256 checksum verification
  - Dependency resolution
  - Multi-repository support
- Fastfetch integration with custom Asombi logo
- Custom shell prompt: `asombi@asombi-root:~#`
- One-command installer (`install.sh`)

© WFWorld
