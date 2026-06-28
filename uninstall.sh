#!/bin/bash
# Asombi OS — Uninstaller

set -e

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
BIN_DIR="$PREFIX/bin"
ASOMBI_DATA="$HOME/.asombi"
WIZZOR_DATA="$HOME/.wizzor"

echo ""
echo "  Asombi OS — Uninstaller"
echo ""

warn() { echo "  [!] $1"; }
ok()   { echo "  [✓] $1"; }

# Удаляем симлинки
for cmd in os wiz; do
    if [ -L "$BIN_DIR/$cmd" ]; then
        rm -f "$BIN_DIR/$cmd"
        ok "Removed command: $cmd"
    fi
done

# Спрашиваем про данные
echo ""
read -r -p "  Remove all Asombi instances and data (~/.asombi)? [y/N] " answer
if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    if [ -d "$ASOMBI_DATA" ]; then
        rm -rf "$ASOMBI_DATA"
        ok "Removed ~/.asombi (instances, configs)"
    fi
    if [ -d "$WIZZOR_DATA" ]; then
        rm -rf "$WIZZOR_DATA"
        ok "Removed ~/.wizzor (packages, cache)"
    fi
else
    warn "Instance data kept at ~/.asombi"
fi

echo ""
ok "Asombi OS uninstalled."
echo ""
