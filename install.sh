#!/bin/bash
# Asombi OS - Installer for Termux / Android ARM64 & x86_64

set -e

REPO="https://github.com/WFStudio-app/Asombi"
INSTALL_DIR="${HOME}/.asombi"
ASOMBI_DIR="${INSTALL_DIR}/Asombi"
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
BIN_DIR="${PREFIX}/bin"

ok()   { echo "  [  OK  ] $1"; }
err()  { echo "  [ FAIL ] $1"; exit 1; }
info() { echo "  [  ..  ] $1"; }
warn() { echo "  [  !!  ] $1"; }

echo ""
echo "  Installing Asombi OS..."
echo ""

# ── Проверка архитектуры ─────────────────────────────────────────
ARCH=$(uname -m)
case "$ARCH" in
    aarch64|arm64) ok "Architecture: ARM64 — fully supported" ;;
    x86_64)        ok "Architecture: x86_64 — supported" ;;
    armv7l|armv8l) warn "Architecture: $ARCH — 32-bit ARM, may have issues" ;;
    *)             err "Unsupported architecture: $ARCH" ;;
esac

# ── Проверка Termux ──────────────────────────────────────────────
if [ -z "$PREFIX" ] || [ ! -d "$PREFIX" ]; then
    err "Termux PREFIX not found. Please run inside Termux."
fi
ok "Termux environment detected"

# ── Python 3 ─────────────────────────────────────────────────────
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    ok "Python $PY_VER found"
else
    info "Python3 not found. Installing..."
    pkg install python -y || err "Failed to install Python3"
    ok "Python3 installed"
fi

# ── Git ──────────────────────────────────────────────────────────
if command -v git >/dev/null 2>&1; then
    ok "Git found"
else
    info "Git not found. Installing..."
    pkg install git -y || err "Failed to install git"
    ok "Git installed"
fi

# ── proot ────────────────────────────────────────────────────────
if command -v proot >/dev/null 2>&1; then
    ok "proot found"
else
    info "Installing proot..."
    pkg install proot -y || err "Failed to install proot"
    ok "proot installed"
fi

# ── Клонирование ─────────────────────────────────────────────────
mkdir -p "${INSTALL_DIR}"

if [ -d "${ASOMBI_DIR}/.git" ]; then
    info "Updating existing installation..."
    git -C "${ASOMBI_DIR}" pull --quiet || warn "Update failed, continuing with existing version"
    ok "Updated"
elif [ -d "${ASOMBI_DIR}" ]; then
    # Папка есть но не git репозиторий — удаляем и клонируем заново
    warn "Found broken installation, reinstalling..."
    rm -rf "${ASOMBI_DIR}"
    git clone "${REPO}" "${ASOMBI_DIR}" --quiet || err "Failed to clone repository"
    ok "Repository cloned"
else
    info "Cloning Asombi repository..."
    git clone "${REPO}" "${ASOMBI_DIR}" --quiet || err "Failed to clone repository"
    ok "Repository cloned"
fi

# ── Проверка что файлы на месте ──────────────────────────────────
[ -f "${ASOMBI_DIR}/bin/os"  ] || err "bin/os not found after clone"
[ -f "${ASOMBI_DIR}/bin/wiz" ] || err "bin/wiz not found after clone"

# ── Права ────────────────────────────────────────────────────────
chmod +x "${ASOMBI_DIR}/bin/os"
chmod +x "${ASOMBI_DIR}/bin/wiz"

# ── Симлинки ─────────────────────────────────────────────────────
ln -sf "${ASOMBI_DIR}/bin/os"  "${BIN_DIR}/os"
ln -sf "${ASOMBI_DIR}/bin/wiz" "${BIN_DIR}/wiz"
ok "Commands registered: os, wiz"

echo ""
ok "Asombi OS installed successfully!"
echo ""
echo "  Quick start:"
echo "    os login asombi-1"
echo ""
echo "  To uninstall:"
echo "    bash ${ASOMBI_DIR}/uninstall.sh"
echo ""
