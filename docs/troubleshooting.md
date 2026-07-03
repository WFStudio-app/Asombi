# Troubleshooting

## Common errors

### `[Process completed (signal 9)]`
Android killed the process. This is an Android 12+ issue with phantom processes.
**Fix:** Disable phantom process killing in Developer Options, or use a lower Android version.

### `proot: cannot open /proc/self/exe`
proot version mismatch.
```bash
pkg upgrade proot -y
```

### `os login` hangs on first boot
Download of Alpine rootfs may be slow. Wait up to 2 minutes.
If it fails, check your internet connection and retry.

### `wiz install` returns "No packages found"
Your sources list may be empty or unreachable.
```bash
wiz repo list
wiz repo add https://raw.githubusercontent.com/WFStudio-app/Asombi/main/packages/index.toml
```

### `Permission denied` on `bin/os` or `bin/wiz`
```bash
chmod +x ~/.asombi/Asombi/bin/os
chmod +x ~/.asombi/Asombi/bin/wiz
```

### Alpine package install fails (`apk add`)
Inside Asombi, update the index first:
```bash
apk update
apk add <package>
```

### `fastfetch: command not found`
```bash
apk add fastfetch
```
If not available in Alpine repos, it falls back to showing the logo directly.

---

## Getting help

- Open an issue: https://github.com/WFStudio-app/Asombi/issues
- Start a discussion: https://github.com/WFStudio-app/Asombi/discussions

---

© WFWorld
