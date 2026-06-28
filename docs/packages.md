# Creating Wizzor Packages

## Package index format

```json
{
  "repo": "My Repo",
  "maintainer": "your-name",
  "updated": "2026-06-28",
  "packages": {
    "my-tool": {
      "version": "1.0.0",
      "description": "Short description (max 80 chars)",
      "url": "https://example.com/my-tool-1.0.0.tar.gz",
      "sha256": "abc123...",
      "size": "200 KB",
      "depends": ["curl"],
      "license": "MIT",
      "post_install": "install.sh"
    }
  }
}
```

## Supported package formats

| Format | Extension |
|--------|-----------|
| Tar gzip | `.tar.gz`, `.tgz` |
| Tar xz | `.tar.xz` |
| Tar bzip2 | `.tar.bz2` |
| Zip | `.zip` |
| Shell script | `.sh` |

## Generating SHA256

```bash
sha256sum my-tool-1.0.0.tar.gz
```

## Post-install script

If your package needs setup after extraction, add a `post_install` field
pointing to a shell script inside your archive:

```bash
#!/bin/sh
# install.sh — runs after extraction inside ~/.wizzor/packages/<name>/
ln -sf "$(pwd)/my-tool" "$PREFIX/bin/my-tool"
```

## Publishing your repo

1. Host `index.json` anywhere (GitHub raw, your server, etc.)
2. Users add it with:
```bash
wiz repo add https://raw.githubusercontent.com/you/repo/main/index.json
```

## Submitting to official index

Open a PR adding your package to `packages/index.json`.

---

© WFWorld
