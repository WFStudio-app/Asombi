#!/bin/bash
# Asombi OS — Installer for Termux / Android ARM64 & x86_64

set -e

REPO="https://github.com/WFStudio-app/Asombi"
INSTALL_DIR="$HOME/.asombi"
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
BIN_DIR="$PREFIX/bin"

ok()   { echo "  [  OK  ] $1"; }
err()  { echo "  [ FAIL ] $1"; exit 1; }
info() { echo "  [  ..  ] $1"; }
warn() { echo "  [  !!  ] $1"; }

echo ""
echo "  ░█████╗░░██████╗░█████╗░███╗░░░███╗██████╗░██╗"
echo "  ██╔══██╗██╔════╝██╔══██╗████╗░████║██╔══██╗██║"
echo "  ███████║╚█████╗░██║░░██║██╔████╔██║██████╦╝██║"
echo "  ██╔══██║░╚═══██╗██║░░██║██║╚██╔╝██║██╔══██╗██║"
echo "  ██║░░██║██████╔╝╚█████╔╝██║░╚═╝░██║██████╦╝██║"
echo "  ╚═╝░░╚═╝╚═════╝░╚════╝░╚═╝░░░╚═╝╚═════╝░╚═╝"
echo "  Installing Asombi OS..."
echo ""

# ── Проверка архитектуры ─────────────────────────────────────────
ARCH=$(uname -m)
case "$ARCH" in
    aarch64|arm64)
        ok "Architecture: ARM64 (aarch64) — fully supported" ;;
    x86_64)
        ok "Architecture: x86_64 — supported" ;;
    armv7l|armv8l)
        warn "Architecture: $ARCH — 32-bit ARM, may have issues" ;;
    *)
        err "Unsupported architecture: $ARCH" ;;
esac

# ── Проверка Android / Termux ────────────────────────────────────
if [ -z "$PREFIX" ] || [ ! -d "$PREFIX" ]; then
    err "Termux PREFIX not found. Please run inside Termux."
fi
ok "Termux environment detected"

# ── Проверка Python 3 ────────────────────────────────────────────
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
    PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]; }; then
        warn "Python $PY_VER found, but 3.8+ recommended. Upgrading..."
        pkg install python -y
    else
        ok "Python $PY_VER found"
    fi
else
    info "Python3 not found. Installing..."
    pkg install python -y
    ok "Python3 installed"
fi

# ── Проверка git ─────────────────────────────────────────────────
if command -v git >/dev/null 2>&1; then
    ok "Git found: $(git --version)"
else
    info "Git not found. Installing..."
    pkg install git -y
    ok "Git installed"
fi

# ── Проверка proot ───────────────────────────────────────────────
if command -v proot >/dev/null 2>&1; then
    ok "proot found"
else
    info "Installing proot..."
    pkg install proot -y
    ok "proot installed"
fi

# ── Клонирование / обновление репозитория ────────────────────────
if [ -d "$INSTALL_DIR/Asombi/.git" ]; then
    info "Updating existing installation..."
    git -C "$INSTALL_DIR/Asombi" pull --quiet
    ok "Updated to latest version"
else
    info "Cloning Asombi repository..."
    mkdir -p "$INSTALL_DIR"
    git clone "$REPO" "$INSTALL_DIR/Asombi" --quiet
    ok "Repository cloned"
fi

# ── Права на исполнение ──────────────────────────────────────────
chmod +x "$INSTALL_DIR/Asombi/bin/os"
chmod +x "$INSTALL_DIR/Asombi/bin/wiz"

# ── Симлинки ─────────────────────────────────────────────────────
ln -sf "$INSTALL_DIR/Asombi/bin/os"  "$BIN_DIR/os"
ln -sf "$INSTALL_DIR/Asombi/bin/wiz" "$BIN_DIR/wiz"
ok "Commands registered: os, wiz"

# ── Версия ───────────────────────────────────────────────────────
echo ""
ok "Asombi OS installed successfully!"
echo ""
echo "  Quick start:"
echo "    os login asombi-1"
echo ""
echo "  To uninstall:"
echo "    bash $INSTALL_DIR/Asombi/uninstall.sh"
echo ""
