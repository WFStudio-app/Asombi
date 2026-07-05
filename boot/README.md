# Asombi Boot (C)

Fast OS entry point written in C. Replaces the Python bin/os.

## Build

```bash
make

make arm64
```

## Install

```bash
make && cp os ../bin/os-bin
```

## Why C

- Zero runtime dependencies
- Starts in <5ms vs ~150ms for Python
- Single static binary
- Direct syscalls via execl/execvp

(c) WFWorld - MIT License
