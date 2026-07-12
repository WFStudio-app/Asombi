#!/bin/bash
# Asombi OS - macOS Installer
# Intel (x86_64) and Apple Silicon (arm64)

set -e

VERSION="0.2.00"
ASOMBI_DIR="${HOME}/.asombi"
ASOMBI_REPO="${ASOMBI_DIR}/Asombi"
REPO="https://github.com/WFStudio-app/Asombi"

GRN="\033[92m"; RED="\033[91m"; YEL="\033[93m"; CYN="\033[96m"; RST="\033[0m"
ok()   { echo -e "  ${GRN}[  OK  ]${RST} $1"; }
err()  { echo -e "  ${RED}[ FAIL ]${RST} $1"; exit 1; }
info() { echo -e "  ${CYN}[  ..  ]${RST} $1"; }
warn() { echo -e "  ${YEL}[  !!  ]${RST} $1"; }

echo ""
echo -e "  ${CYN}Asombi OS v${VERSION} — macOS Installer${RST}"
echo ""

# ── Платформа ────────────────────────────────────────────────────
ARCH=$(uname -m)
OS_VER=$(sw_vers -productVersion 2>/dev/null || echo "unknown")
case "$ARCH" in
    arm64)  ok "Apple Silicon (M1/M2/M3) — $OS_VER" ;;
    x86_64) ok "Intel Mac — $OS_VER" ;;
    *)      err "Unknown arch: $ARCH" ;;
esac

# ── Homebrew ─────────────────────────────────────────────────────
if ! command -v brew >/dev/null 2>&1; then
    info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" \
        || err "Homebrew install failed"
    # Apple Silicon path
    [ -f /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
    ok "Homebrew installed"
else
    ok "Homebrew: $(brew --version | head -1)"
fi

# ── Зависимости ──────────────────────────────────────────────────
for pkg in python3 git lima; do
    if ! command -v "$pkg" >/dev/null 2>&1; then
        info "Installing $pkg..."
        brew install "$pkg" || err "Failed to install $pkg"
        ok "$pkg installed"
    else
        ok "$pkg found"
    fi
done

# ── Свободное место ──────────────────────────────────────────────
FREE_MB=$(df -m "${HOME}" | awk 'NR==2{print $4}')
[ "$FREE_MB" -lt 500 ] && err "Not enough space: ${FREE_MB}MB, need 500MB"
ok "Disk: ${FREE_MB}MB free"

# ── Клонирование ─────────────────────────────────────────────────
mkdir -p "${ASOMBI_DIR}"
SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
if [ -f "${SCRIPT_DIR}/bin/os" ] && [ -f "${SCRIPT_DIR}/bin/trk" ]; then
    [ "${SCRIPT_DIR}" != "${ASOMBI_REPO}" ] && {
        rm -rf "${ASOMBI_REPO}" 2>/dev/null || true
        ln -sf "${SCRIPT_DIR}" "${ASOMBI_REPO}"
        ok "Linked existing clone"
    }
elif [ -d "${ASOMBI_REPO}/.git" ]; then
    info "Updating..."
    git -C "${ASOMBI_REPO}" pull --quiet 2>&1 | tail -3 || warn "Update failed"
    ok "Updated"
else
    info "Cloning Asombi..."
    git clone "$REPO" "${ASOMBI_REPO}" 2>&1 | tail -3 || err "Clone failed"
    ok "Cloned"
fi

[ -f "${ASOMBI_REPO}/bin/os"  ] || err "bin/os not found"
[ -f "${ASOMBI_REPO}/bin/trk" ] || err "bin/trk not found"
chmod 755 "${ASOMBI_REPO}/bin/os" "${ASOMBI_REPO}/bin/trk"
ok "Permissions set"

# ── Lima конфиг ──────────────────────────────────────────────────
# Lima запускает лёгкую Linux VM на macOS без Docker
LIMA_CFG_DIR="${HOME}/.lima/asombi"
mkdir -p "${LIMA_CFG_DIR}"

cat > "${LIMA_CFG_DIR}/lima.yaml" << LIMA
# Asombi OS Lima VM
vmType: qemu
os: Linux
arch: default
images:
  - location: "https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/x86_64/alpine-virt-3.19.0-x86_64.iso"
    arch: "x86_64"
  - location: "https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/aarch64/alpine-virt-3.19.0-aarch64.iso"
    arch: "aarch64"
cpus: 2
memory: "1GiB"
disk: "10GiB"
mounts:
  - location: "~"
    writable: true
ssh:
  localPort: 60222
  loadDotSSHPubKeys: true
provision:
  - mode: system
    script: |
      #!/bin/sh
      apk update -q 2>/dev/null
      apk add --no-cache python3 proot curl git busybox -q 2>/dev/null
      chmod 755 "${ASOMBI_REPO}/bin/os" "${ASOMBI_REPO}/bin/trk"
LIMA
ok "Lima VM config created"

# ── Регистрируем команды ─────────────────────────────────────────
# На macOS os и trk запускаются напрямую через python3
# Lima VM используется только для os login (запуск Alpine)
LOCAL_BIN="/usr/local/bin"
if [ ! -w "$LOCAL_BIN" ]; then
    LOCAL_BIN="${HOME}/.local/bin"
    mkdir -p "$LOCAL_BIN"
    SHELL_RC="${HOME}/.zshrc"
    grep -q "$LOCAL_BIN" "$SHELL_RC" 2>/dev/null \
        || echo "export PATH=\"$LOCAL_BIN:\$PATH\"" >> "$SHELL_RC"
fi

for CMD in os trk; do
    TARGET="${LOCAL_BIN}/${CMD}"
    [ -e "$TARGET" ] && ! grep -q "Asombi" "$TARGET" 2>/dev/null && {
        warn "${TARGET} belongs to another program — skipping"
        continue
    }
    printf '#!/bin/bash\nexec python3 "%s/bin/%s" "$@"\n' "${ASOMBI_REPO}" "$CMD" > "$TARGET"
    chmod 755 "$TARGET"
    ok "Command: $CMD → $TARGET"
done

echo ""
ok "Asombi OS installed for macOS!"
echo ""
echo "  Quick start:"
echo "    os login asombi-1"
echo ""
echo "  Note: first boot downloads Alpine (~50MB) via Lima VM"
echo "  Uninstall: bash ${ASOMBI_REPO}/uninstall-macos.sh"
echo ""
