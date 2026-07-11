#!/bin/bash
# Asombi OS - Uninstaller

set -e

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
BIN_DIR="${PREFIX}/bin"
ASOMBI_DATA="${HOME}/.asombi"

ok()   { echo "  [OK] $1"; }
warn() { echo "  [!!] $1"; }

echo ""
echo "  Asombi OS - Uninstaller"
echo ""

# БАГ 4 ФИКС: удаляем os и trk (было: os и wiz — неверно)
for cmd in os trk; do
    TARGET="${BIN_DIR}/${cmd}"
    if [ -L "${TARGET}" ]; then
        LINK_DEST=$(readlink "${TARGET}")
        if echo "${LINK_DEST}" | grep -q "asombi\|Asombi"; then
            rm -f "${TARGET}"
            ok "Removed symlink: ${cmd}"
        else
            warn "Skipping ${cmd} — points to ${LINK_DEST} (not Asombi)"
        fi
    elif [ -f "${TARGET}" ]; then
        # Wrapper скрипт (не симлинк)
        if grep -q "asombi\|Asombi" "${TARGET}" 2>/dev/null; then
            rm -f "${TARGET}"
            ok "Removed command: ${cmd}"
        else
            warn "Skipping ${cmd} — not an Asombi command"
        fi
    fi
done

echo ""
read -r -p "  Remove all Asombi data (~/.asombi)? [y/N] " answer
if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    [ -d "${ASOMBI_DATA}" ] && rm -rf "${ASOMBI_DATA}" && ok "Removed ~/.asombi"
else
    warn "Data kept at ~/.asombi"
fi

echo ""
ok "Asombi OS uninstalled."
echo ""
