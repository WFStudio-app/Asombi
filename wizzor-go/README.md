# Wizzor (Go rewrite)

Wizzor package manager rewritten in Go — replaces the Python version incrementally.

## Status

| Etap | Commands | Status |
|------|----------|--------|
| 1 | `wiz version`, `wiz help` | Done |
| 2 | `wiz search`, `wiz list` | Done |
| 3 | `wiz install`, `wiz remove` | Pending |
| 4 | `wiz update`, `wiz repo` | Pending |
| 5 | Parallel downloads (goroutines) | Pending |

## Platform support

| OS | Arch | Status |
|----|------|--------|
| Linux | amd64 | Supported |
| Linux | arm64 (Termux/Android) | Supported |
| Windows | amd64 | Supported |
| macOS | amd64 / arm64 | Supported |

## Build

```bash
# Host
go build -o wiz ./cmd/wiz/

# ARM64 (Termux/Android)
GOOS=linux GOARCH=arm64 go build -o wiz-arm64 ./cmd/wiz/

# Windows
GOOS=windows GOARCH=amd64 go build -o wiz.exe ./cmd/wiz/

# macOS
GOOS=darwin GOARCH=arm64 go build -o wiz-macos ./cmd/wiz/
```

CI automatically builds binaries for all platforms on every push — see
`.github/workflows/build-wizzor.yml`.

## Structure

```
wizzor-go/
├── cmd/wiz/
│   ├── main.go                  <- Entry point, command router
│   └── commands/
│       ├── search.go            <- wiz search
│       └── list.go              <- wiz list
├── internal/
│   ├── output/
│   │   ├── output.go            <- Colors, print helpers
│   │   ├── ansi_windows.go      <- Windows ANSI enable (build tag)
│   │   └── ansi_unix.go         <- Unix no-op (build tag)
│   ├── config/config.go         <- Cross-platform paths
│   ├── toml/toml.go             <- Custom TOML parser (no deps)
│   ├── repo/                    <- Package index types + parser
│   ├── sources/sources.go       <- Repository list management
│   ├── fetch/fetch.go           <- HTTP downloads
│   └── db/installed.go          <- Installed packages DB
└── go.mod
```

## Package index format (TOML)

```toml
[repo]
name = "My Repo"
maintainer = "you"
updated = "2026-06-30"

[packages.curl]
version = "8.9.1"
description = "HTTP transfer tool"
url = "https://example.com/curl.tar.gz"
sha256 = "abc123..."
size = "500 KB"
depends = ["openssl"]
license = "MIT"
```

(c) WFWorld - MIT License
