#!/bin/bash
# Wizzor installer for Termux / Android ARM64

set -e

REPO="https://github.com/WFStudio-app/Asombi"
INSTALL_DIR="$HOME/.wizzor"
BIN_DIR="$PREFIX/bin"  # Termux uses $PREFIX

echo "  ██╗    ██╗██╗███████╗███████╗ ██████╗ ██████╗"
echo "  ██║    ██║██║╚══███╔╝╚══███╔╝██╔═══██╗██╔══██╗"
echo "  ██║ █╗ ██║██║  ███╔╝   ███╔╝ ██║   ██║██████╔╝"
echo "  ██║███╗██║██║ ███╔╝   ███╔╝  ██║   ██║██╔══██╗"
echo "  ╚███╔███╔╝██║███████╗███████╗╚██████╔╝██║  ██║"
echo "   ╚══╝╚══╝ ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝"
echo ""
echo "  Installing Wizzor Package Manager..."
echo ""

# Проверка python3
if ! command -v python3 &>/dev/null; then
    echo "[!] Python3 not found. Installing..."
    pkg install python -y
fi

# Проверка git
if ! command -v git &>/dev/null; then
    echo "[!] Git not found. Installing..."
    pkg install git -y
fi

# Клонирование репозитория
if [ -d "$INSTALL_DIR/Asombi" ]; then
    echo "[i] Updating existing installation..."
    git -C "$INSTALL_DIR/Asombi" pull
else
    echo "[i] Cloning Asombi repository..."
    mkdir -p "$INSTALL_DIR"
    git clone "$REPO" "$INSTALL_DIR/Asombi"
fi

# Создание симлинков
ln -sf "$INSTALL_DIR/Asombi/bin/wiz" "$BIN_DIR/wiz"
ln -sf "$INSTALL_DIR/Asombi/bin/os"  "$BIN_DIR/os"
chmod +x "$INSTALL_DIR/Asombi/bin/wiz"
chmod +x "$INSTALL_DIR/Asombi/bin/os"

echo ""
echo "[✓] Wizzor installed successfully!"
echo "[✓] Run: wiz help"
