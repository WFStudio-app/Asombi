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

# ── Архитектура ──────────────────────────────────────────────────
ARCH=$(uname -m)
case "$ARCH" in
    aarch64|arm64) ok "Architecture: ARM64" ;;
    x86_64)        ok "Architecture: x86_64" ;;
    armv7l|armv8l) warn "Architecture: $ARCH — 32-bit, may have issues" ;;
    *)             err "Unsupported architecture: $ARCH" ;;
esac

# ── Termux ───────────────────────────────────────────────────────
if [ -z "$PREFIX" ] || [ ! -d "$PREFIX" ]; then
    err "Termux PREFIX not found. Please run inside Termux."
fi
ok "Termux environment detected"

# ── Android 12+ предупреждение ───────────────────────────────────
ANDROID_SDK=$(getprop ro.build.version.sdk 2>/dev/null || echo "0")
if [ "$ANDROID_SDK" -ge 31 ] 2>/dev/null; then
    warn "Android 12+ detected — Phantom Process Killer may interrupt install"
    warn "If install fails: Developer Options → disable phantom process killing"
fi

# ── БАГ 5 ФИКС: один вызов python3 вместо трёх ──────────────────
if command -v python3 >/dev/null 2>&1; then
    PY_INFO=$(python3 -c "import sys; v=sys.version_info; print(f'{v.major}.{v.minor}', v.major, v.minor)")
    PY_VER=$(echo "$PY_INFO" | awk '{print $1}')
    PY_MAJ=$(echo "$PY_INFO" | awk '{print $2}')
    PY_MIN=$(echo "$PY_INFO" | awk '{print $3}')
    if [ "$PY_MAJ" -lt 3 ] || { [ "$PY_MAJ" -eq 3 ] && [ "$PY_MIN" -lt 8 ]; }; then
        warn "Python $PY_VER found, need 3.8+. Upgrading..."
        pkg install python -y || err "Failed to install Python"
    else
        ok "Python $PY_VER found"
    fi
else
    info "Python3 not found. Installing..."
    pkg install python -y || err "Failed to install Python"
    ok "Python3 installed"
fi

# ── Git ──────────────────────────────────────────────────────────
if command -v git >/dev/null 2>&1; then
    ok "Git found"
else
    info "Installing git..."
    pkg install git -y || err "Failed to install git"
    ok "Git installed"
fi

# ── proot — с проверкой версии ───────────────────────────────────
if command -v proot >/dev/null 2>&1; then
    PROOT_VER=$(proot --version 2>&1 | head -1 || echo "unknown")
    ok "proot found: $PROOT_VER"
else
    info "Installing proot..."
    pkg install proot -y || err "Failed to install proot"
    ok "proot installed"
fi

# ── БАГ 9 ФИКС: проверка свободного места ────────────────────────
FREE_KB=$(df -k "${HOME}" 2>/dev/null | awk 'NR==2{print $4}' || echo "0")
FREE_MB=$((FREE_KB / 1024))
if [ "$FREE_MB" -lt 150 ]; then
    err "Not enough disk space: ${FREE_MB}MB free, need at least 150MB"
fi
ok "Disk space: ${FREE_MB}MB free"

# ── БАГ 1+2+8 ФИКС: клонирование с диагностикой ─────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
if [ -f "${SCRIPT_DIR}/bin/os" ] && [ -f "${SCRIPT_DIR}/bin/trk" ]; then
    if [ "${SCRIPT_DIR}" != "${ASOMBI_DIR}" ]; then
        info "Using existing clone at ${SCRIPT_DIR}"
        mkdir -p "${INSTALL_DIR}"
        rm -rf "${ASOMBI_DIR}" 2>/dev/null || true
        ln -sf "${SCRIPT_DIR}" "${ASOMBI_DIR}" 2>/dev/null \
            || cp -r "${SCRIPT_DIR}/." "${ASOMBI_DIR}/"
        ok "Linked existing clone"
    fi
elif [ -d "${ASOMBI_DIR}/.git" ]; then
    info "Updating existing installation..."
    git -C "${ASOMBI_DIR}" pull --quiet 2>&1 | head -5 \
        || warn "Update failed — continuing with existing version"
    ok "Updated"
elif [ -d "${ASOMBI_DIR}" ] && [ ! -d "${ASOMBI_DIR}/.git" ]; then
    warn "Broken installation found — reinstalling"
    rm -rf "${ASOMBI_DIR}"
    mkdir -p "${INSTALL_DIR}"
    info "Cloning Asombi..."
    git clone "${REPO}" "${ASOMBI_DIR}" 2>&1 | tail -3 \
        || err "Failed to clone — check internet connection"
    ok "Repository cloned"
else
    mkdir -p "${INSTALL_DIR}"
    info "Cloning Asombi..."
    git clone "${REPO}" "${ASOMBI_DIR}" 2>&1 | tail -3 \
        || err "Failed to clone — check internet connection"
    ok "Repository cloned"
fi

# ── БАГ 3 ФИКС: проверяем файлы перед chmod ─────────────────────
[ -f "${ASOMBI_DIR}/bin/os"  ] || err "bin/os not found after clone"
[ -f "${ASOMBI_DIR}/bin/trk" ] || err "bin/trk not found after clone"

chmod 755 "${ASOMBI_DIR}/bin/os"
chmod 755 "${ASOMBI_DIR}/bin/trk"
find "${ASOMBI_DIR}/truck/core/" -name "*.py" -exec chmod 644 {} \; 2>/dev/null || true
ok "Permissions set"

# ── БАГ 1 ФИКС: wrapper вместо симлинка — нет конфликтов ─────────
for CMD in os trk; do
    TARGET="${BIN_DIR}/${CMD}"
    SRC="${ASOMBI_DIR}/bin/${CMD}"

    if [ ! -f "${SRC}" ]; then
        err "Source not found: ${SRC}"
    fi

    # Проверяем конфликт — если файл есть и не наш wrapper
    if [ -e "${TARGET}" ] && [ ! -L "${TARGET}" ]; then
        EXISTING_CONTENT=$(head -2 "${TARGET}" 2>/dev/null || echo "")
        if echo "$EXISTING_CONTENT" | grep -q "asombi\|Asombi"; then
            rm -f "${TARGET}"
        else
            warn "${TARGET} exists and belongs to another program — skipping"
            warn "Remove manually if needed: rm ${TARGET}"
            continue
        fi
    else
        rm -f "${TARGET}"
    fi

    printf '#!/bin/sh\nexec python3 "%s" "$@"\n' "${SRC}" > "${TARGET}"
    chmod 755 "${TARGET}"
    ok "Command registered: ${CMD}"
done

echo ""
ok "Asombi OS installed!"
echo ""
echo "  Quick start:  os login asombi-1"
echo "  Uninstall:    bash ${ASOMBI_DIR}/uninstall.sh"
echo ""
