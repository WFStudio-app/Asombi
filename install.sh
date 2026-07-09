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

# ── Android 12+ Phantom Process Killer предупреждение ────────────
ANDROID_VER=$(getprop ro.build.version.release 2>/dev/null || echo "0")
ANDROID_SDK=$(getprop ro.build.version.sdk 2>/dev/null || echo "0")
if [ "$ANDROID_SDK" -ge 31 ] 2>/dev/null; then
    echo ""
    warn "Android 12+ detected (API $ANDROID_SDK)"
    warn "Phantom Process Killer may terminate long-running processes."
    warn "If installation fails mid-way, go to:"
    warn "  Developer Options → disable 'Phantom process killing'"
    warn "  or run: adb shell device_config set_sync_disabled_for_tests persistent"
    echo ""
fi

# ── Python 3 — один вызов ────────────────────────────────────────
if command -v python3 >/dev/null 2>&1; then
    PY_INFO=$(python3 -c "
import sys
v = sys.version_info
print(f'{v.major}.{v.minor}', v.major, v.minor)
")
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

# ── proot ────────────────────────────────────────────────────────
if command -v proot >/dev/null 2>&1; then
    ok "proot found"
else
    info "Installing proot..."
    pkg install proot -y || err "Failed to install proot"
    ok "proot installed"
fi

# ── БАГ 1 ФИКС: идемпотентное клонирование ──────────────────────
# Если install.sh запущен из уже клонированной папки Asombi —
# используем её, не клонируем заново.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "${SCRIPT_DIR}/bin/os" ] && [ -f "${SCRIPT_DIR}/bin/trk" ]; then
    # Запущен из клонированной папки — просто линкуем отсюда
    if [ "${SCRIPT_DIR}" != "${ASOMBI_DIR}" ]; then
        info "Using existing clone at ${SCRIPT_DIR}"
        # Создаём симлинк на папку чтобы os/wiz всегда были в ASOMBI_DIR
        mkdir -p "${INSTALL_DIR}"
        # Busybox-совместимый способ: rm + ln -sf
        rm -rf "${ASOMBI_DIR}" 2>/dev/null || true
        ln -sf "${SCRIPT_DIR}" "${ASOMBI_DIR}" 2>/dev/null \
            || cp -r "${SCRIPT_DIR}/." "${ASOMBI_DIR}/"
        ok "Linked existing clone"
    fi
elif [ -d "${ASOMBI_DIR}/.git" ]; then
    info "Updating existing installation..."
    git -C "${ASOMBI_DIR}" pull --quiet \
        || warn "Update failed, continuing with existing version"
    ok "Updated"
elif [ -d "${ASOMBI_DIR}" ] && [ ! -d "${ASOMBI_DIR}/.git" ]; then
    warn "Found broken installation at ${ASOMBI_DIR}, reinstalling..."
    rm -rf "${ASOMBI_DIR}"
    git clone "${REPO}" "${ASOMBI_DIR}" --quiet \
        || err "Failed to clone repository"
    ok "Repository cloned"
else
    info "Cloning Asombi repository..."
    mkdir -p "${INSTALL_DIR}"
    git clone "${REPO}" "${ASOMBI_DIR}" --quiet \
        || err "Failed to clone repository"
    ok "Repository cloned"
fi

# ── Проверка файлов ──────────────────────────────────────────────
[ -f "${ASOMBI_DIR}/bin/os"  ] || err "bin/os not found"
[ -f "${ASOMBI_DIR}/bin/trk" ] || err "bin/trk not found"
chmod 755 "${ASOMBI_DIR}/bin/os"
chmod 755 "${ASOMBI_DIR}/bin/trk"

# ── БАГ 6 ФИКС: симлинки не перезаписывают чужие файлы ──────────
for CMD in os trk; do
    TARGET="${BIN_DIR}/${CMD}"
    if [ -e "${TARGET}" ] && [ ! -L "${TARGET}" ]; then
        warn "${TARGET} exists and is not a symlink — skipping to avoid overwrite"
        warn "Remove it manually if you want Asombi's ${CMD}: rm ${TARGET}"
    else
        ln -sf "${ASOMBI_DIR}/bin/${CMD}" "${TARGET}"
        ok "Command registered: ${CMD}"
    fi
done

echo ""
ok "Asombi OS installed successfully!"
echo ""
echo "  Quick start:  os login asombi-1"
echo "  Uninstall:    bash ${ASOMBI_DIR}/uninstall.sh"
echo ""
