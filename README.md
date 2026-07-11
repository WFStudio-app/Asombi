```
                                       
                                       
                                       
                   =                   
                  ===                  
                == = ==                
               == === ==               
              == == ==                 
             == == =                   
            == == =-= == ==            
           == == =- -= == ==           
          ==== ==     == ====          
         ==                 ==         
       ==.== ==         == == ==       
      == == ==           == == ==      
     == == ==             == == ==     
    == == ==               == == ==    
                                       
                                       
                                       
```

<h1 align="center">ASOMBI OS</h1>
<p align="center">
  Independent Linux environment · ARM64 · x86_64 · Android/Termux
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Version-0.2.00-purple?style=flat-square"/>
  <img src="https://img.shields.io/badge/Package_Manager-Truck-cyan?style=flat-square"/>
  <img src="https://img.shields.io/badge/Boot-C-blue?style=flat-square"/>
  <img src="https://img.shields.io/badge/Loader-Rust-orange?style=flat-square"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square"/>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Android%2FTermux-ARM64-green?style=flat-square&logo=android"/>
  <img src="https://img.shields.io/badge/Linux-x86__64-blue?style=flat-square&logo=linux"/>
</p>

---

## What is Asombi OS?

Asombi is a real Linux environment that runs on top of Android, macOS, Linux and Windows.
No root required. Uses `proot` (Android/Linux) or Docker (macOS/Windows) to boot an
isolated environment with **Truck** — our own package manager.

```
asombi@asombi-root:~#
```

---

## Platform support

| Platform | Method | Status |
|----------|--------|--------|
| Android (Termux) ARM64 | proot | Supported |
| Android (Termux) x86_64 | proot | Supported |
| Linux x86_64 | proot / native | Supported |

---

## Installation

### Android (Termux)

```bash
pkg update && pkg upgrade -y
pkg install git python proot -y
git clone https://github.com/WFStudio-app/Asombi.git
cd Asombi && bash install.sh
os login asombi-1
```

### Linux

```bash
git clone https://github.com/WFStudio-app/Asombi.git
cd Asombi && bash install.sh
os login asombi-1
```

---

## Usage

```bash
os login <name>         # Start or create instance
os delete <name>        # Delete instance
os instances            # List all instances
os version              # Show version
.bios                   # Open BIOS settings
```

### Inside Asombi

```bash
trk install <package>   # Install package
trk remove  <package>   # Remove package
trk update              # Update all packages
trk search  <query>     # Search packages
trk list                # List installed
trk info    <package>   # Package info
trk repo add <url>      # Add repository
trk clean               # Clear cache
```

---

## Architecture

```
Asombi OS
├── bin/os          C — fast boot, no Python dependency
├── bin/trk         Python — Truck package manager
├── truck/core/     Package manager modules
├── loader/         Rust — direct Linux namespaces (replaces proot)
├── boot/           C — boot source code
├── assets/         Logos, fastfetch config
├── packages/       index.toml — official package registry
└── docs/           Documentation
```

---

## Versioning

| Version | Type |
|---------|------|
| `0.X.01` | Mini update |
| `0.X.10` | Major update |
| `0.X.00` | New release |

Current: **0.2.00**

---

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/faq.md](docs/faq.md) | FAQ |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Troubleshooting |
| [docs/wizzor.md](docs/wizzor.md) | Truck command reference |
| [docs/packages.md](docs/packages.md) | Creating packages |
| [docs/architecture.md](docs/architecture.md) | Architecture |

---

## License

MIT — © WFWorld
