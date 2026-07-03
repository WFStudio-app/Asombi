# Wizzor — Package Manager

Wizzor is the built-in package manager for Asombi OS.


## Implementation status

Wizzor is currently being rewritten from Python to Go (`wizzor-go/`).

| Command | Python (active) | Go (in progress) |
|---------|----------------|------------------|
| `wiz install` | ✅ Working | 🔜 Etap 3 |
| `wiz remove` | ✅ Working | 🔜 Etap 3 |
| `wiz update` | ✅ Working | 🔜 Etap 4 |
| `wiz search` | ✅ Working | ✅ Done |
| `wiz list` | ✅ Working | ✅ Done |
| `wiz info` | ✅ Working | 🔜 Etap 3 |
| `wiz repo` | ✅ Working | 🔜 Etap 4 |
| `wiz clean` | ✅ Working | 🔜 Etap 3 |
| `wiz version` | ✅ Working | ✅ Done |

**Currently `bin/wiz` runs the Python version.** The Go binary will replace it
when all commands reach parity.

## Commands

### wiz install
```bash
wiz install curl
wiz install curl git python3
```
Downloads and installs packages including dependencies.

### wiz remove
```bash
wiz remove curl
```

### wiz update
```bash
wiz update          # Update all packages
wiz update curl     # Update specific package
```

### wiz search
```bash
wiz search http
```

### wiz list
```bash
wiz list
```

### wiz info
```bash
wiz info curl
```

### wiz repo
```bash
wiz repo list
wiz repo add https://example.com/repo/index.json
wiz repo remove https://example.com/repo/index.json
```

### wiz clean
```bash
wiz clean
```

## Repository index format

```json
{
  "repo": "Name",
  "maintainer": "author",
  "updated": "2026-06-28",
  "packages": {
    "package-name": {
      "version": "1.0.0",
      "description": "Short description",
      "url": "https://...",
      "sha256": "hex...",
      "size": "100 KB",
      "depends": [],
      "license": "MIT"
    }
  }
}
```

## Data locations (inside Asombi)

| Path | Description |
|------|-------------|
| `~/.wizzor/installed.json` | Installed packages DB |
| `~/.wizzor/sources.list` | Repository list |
| `~/.wizzor/cache/` | Downloaded package cache |
| `~/.wizzor/packages/` | Extracted packages |

© WFWorld
