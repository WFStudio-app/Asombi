# Contributing to Asombi OS

Thank you for your interest in contributing!

## How to contribute

1. Fork the repository
2. Create a branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Commit: `git commit -m "feat: add my feature"`
5. Push: `git push origin feature/my-feature`
6. Open a Pull Request

## Commit convention

| Prefix | Use for |
|--------|---------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `refactor:` | Code refactor |
| `chore:` | Maintenance |

## Adding a Wizzor package

Add your package to `packages/index.json` following the existing format, then open a PR.

## Code style

- Python: follow PEP8
- Shell: POSIX-compatible sh where possible
- Keep it lightweight — this runs on mobile ARM64

## Issues

Use GitHub Issues for bug reports and feature requests.
Please include your Android version and architecture (`uname -m`).

© WFWorld
