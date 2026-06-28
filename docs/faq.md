# FAQ — Frequently Asked Questions

## Installation

**Q: Can I run Asombi without root?**
Yes. Asombi uses `proot` which requires no root access on your device.

**Q: Which Android versions are supported?**
Android 7.0 (API 24) and above. ARM64 and x86_64 architectures.

**Q: How much storage does Asombi use?**
The Alpine Linux base is ~30 MB. Additional packages vary.

---

## Usage

**Q: How do I start Asombi?**
```bash
os login asombi-1
```

**Q: Can I have multiple environments?**
Yes. Each instance is fully isolated:
```bash
os login dev
os login tools
os login test
```

**Q: How do I install packages inside Asombi?**
```bash
wiz install <package>   # Wizzor packages
apk add <package>       # Alpine native packages
```

**Q: Can I access my Termux files from inside Asombi?**
Yes. Your Termux home is mounted at `/termux-home` inside every instance.

---

## Wizzor

**Q: Where does Wizzor download packages from?**
From the official Asombi index and any repos you add with `wiz repo add <url>`.

**Q: How do I publish my own package?**
Host a JSON index file and add it: `wiz repo add https://your-server/index.json`
See [docs/wizzor.md](wizzor.md) for the index format.

**Q: Does Wizzor verify packages?**
Yes. SHA256 checksums are verified before installation if provided in the index.

---

## Troubleshooting

**Q: `proot` not found after install**
```bash
pkg install proot -y
```

**Q: `os: command not found`**
Re-run the installer: `bash install.sh`

**Q: Download fails inside Asombi**
Check `/etc/resolv.conf` inside the instance:
```bash
cat /etc/resolv.conf
# Should contain: nameserver 8.8.8.8
```

**Q: How do I completely remove Asombi?**
```bash
bash ~/.asombi/Asombi/uninstall.sh
```

---

© WFWorld
