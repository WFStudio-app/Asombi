# Asombi OS

> A lightweight operating environment for Termux on Android (ARM64)

## Wizzor — Package Manager

Wizzor is the built-in package manager for Asombi. It lets you install, remove, update, and search packages from multiple repositories — similar to `dnf` or `apt`.

### Quick Install (Termux)

```bash
curl -sL https://raw.githubusercontent.com/WFStudio-app/Asombi/main/install.sh | bash
```

### Usage

```bash
wiz install <package>       # Install a package
wiz remove  <package>       # Remove a package
wiz update                  # Update all packages
wiz update  <package>       # Update specific package
wiz search  <query>         # Search packages
wiz list                    # List installed packages
wiz info    <package>       # Show package details
wiz repo    list            # List repositories
wiz repo    add    <url>    # Add a repository
wiz repo    remove <url>    # Remove a repository
wiz clean                   # Clear download cache
wiz version                 # Show version
```

### Repository Format

Repositories are JSON files with this structure:

```json
{
  "repo": "My Repo",
  "maintainer": "you",
  "packages": {
    "my-package": {
      "version": "1.0.0",
      "description": "What it does",
      "url": "https://example.com/my-package.tar.gz",
      "sha256": "abc123...",
      "size": "200 KB",
      "depends": [],
      "license": "MIT"
    }
  }
}
```

## Project Structure

```
Asombi/
├── bin/wiz              — Main executable
├── wizzor/core/         — Command modules
├── packages/index.json  — Official package index
├── install.sh           — One-line installer
└── README.md
```

## Requirements

- Android with Termux
- Python 3.x
- ARM64 architecture

## License

MIT © WFStudio-app
