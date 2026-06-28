#!/bin/sh
# Asombi OS - fastfetch setup script
# Запускается внутри Alpine при первом boot

set -e

CYAN="\033[96m"
GREEN="\033[92m"
RESET="\033[0m"

echo "${CYAN}[Asombi]${RESET} Setting up fastfetch..."

# Обновляем apk
apk update -q

# Устанавливаем fastfetch
apk add fastfetch -q 2>/dev/null || {
    # Если нет в репах — собираем легковесную альтернативу
    echo "${CYAN}[Asombi]${RESET} fastfetch not in repos, using neofetch fallback..."
    apk add neofetch -q 2>/dev/null || apk add bash curl -q
}

# Копируем конфиг fastfetch
mkdir -p /root/.config/fastfetch
cp /opt/asombi/assets/fastfetch.jsonc /root/.config/fastfetch/config.jsonc

# Копируем логотип
mkdir -p /root/.asombi
cp /opt/asombi/assets/logo.txt /root/.asombi/logo.txt

echo "${GREEN}[  OK  ]${RESET} fastfetch configured"
