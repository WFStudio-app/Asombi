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

# Удаляем симлинки только если они указывают на Asombi
for cmd in os wiz; do
    TARGET="${BIN_DIR}/${cmd}"
    if [ -L "${TARGET}" ]; then
        LINK_DEST=$(readlink "${TARGET}")
        if echo "${LINK_DEST}" | grep -q "asombi\|Asombi"; then
            rm -f "${TARGET}"
            ok "Removed command: ${cmd}"
        else
            warn "Skipping ${cmd} — points to ${LINK_DEST} (not Asombi)"
        fi
    fi
done

echo ""
read -r -p "  Remove all Asombi data (~/.asombi)? [y/N] " answer
if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    if [ -d "${ASOMBI_DATA}" ]; then
        rm -rf "${ASOMBI_DATA}"
        ok "Removed ~/.asombi (instances, packages, cache, data)"
    fi
else
    warn "Data kept at ~/.asombi"
fi

echo ""
ok "Asombi OS uninstalled."
echo ""
