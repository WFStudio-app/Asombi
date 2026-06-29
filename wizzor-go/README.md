# Wizzor (Go rewrite)

Wizzor package manager rewritten in Go — replaces the Python version incrementally.

## Status

| Etap | Commands | Status |
|------|----------|--------|
| 1 | `wiz version`, `wiz help` | ✅ Done |
| 2 | `wiz search`, `wiz list` | 🔜 Next |
| 3 | `wiz install`, `wiz remove` | ⏳ Pending |
| 4 | `wiz update`, `wiz repo` | ⏳ Pending |
| 5 | Parallel downloads (goroutines) | ⏳ Pending |

## Build

```bash
# Host
go build -o wiz ./cmd/wiz/

# ARM64 (Termux/Android)
GOOS=linux GOARCH=arm64 go build -o wiz-arm64 ./cmd/wiz/
```

## Structure

```
wizzor-go/
├── cmd/wiz/main.go              <- Entry point, command router
├── internal/
│   ├── output/output.go         <- Colors, print helpers
│   └── config/config.go         <- Paths, defaults
└── go.mod
```

(c) WFWorld - MIT License
