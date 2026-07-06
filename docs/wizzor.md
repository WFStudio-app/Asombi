# Truck — Package Manager

Truck is the built-in package manager for Asombi OS.


## Implementation status

Truck is currently being rewritten from Python to Go (`truck-go/`).

| Command | Python (active) | Go (in progress) |
|---------|----------------|------------------|
| `trk install` | ✅ Working | 🔜 Etap 3 |
| `trk remove` | ✅ Working | 🔜 Etap 3 |
| `trk update` | ✅ Working | 🔜 Etap 4 |
| `trk search` | ✅ Working | ✅ Done |
| `trk list` | ✅ Working | ✅ Done |
| `trk info` | ✅ Working | 🔜 Etap 3 |
| `trk repo` | ✅ Working | 🔜 Etap 4 |
| `trk clean` | ✅ Working | 🔜 Etap 3 |
| `trk version` | ✅ Working | ✅ Done |

**Currently `bin/trk` runs the Python version.** The Go binary will replace it
when all commands reach parity.

## Commands

### trk install
```bash
trk install curl
trk install curl git python3
```
Downloads and installs packages including dependencies.

### trk remove
```bash
trk remove curl
```

### trk update
```bash
trk update          # Update all packages
trk update curl     # Update specific package
```

### trk search
```bash
trk search http
```

### trk list
```bash
trk list
```

### trk info
```bash
trk info curl
```

### trk repo
```bash
trk repo list
trk repo add https://example.com/repo/index.json
trk repo remove https://example.com/repo/index.json
```

### trk clean
```bash
trk clean
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
| `~/.truck/installed.json` | Installed packages DB |
| `~/.truck/sources.list` | Repository list |
| `~/.truck/cache/` | Downloaded package cache |
| `~/.truck/packages/` | Extracted packages |

© WFWorld
