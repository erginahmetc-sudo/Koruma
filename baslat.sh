#!/usr/bin/env bash
# Koruma'yı başlatır (setup.sh zaten çalıştırılmış olmalı)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -d "$ROOT/desktop/node_modules" ]; then
    echo "Önce ./setup.sh dosyasını çalıştırmanız gerekiyor."
    exit 1
fi
cd "$ROOT/desktop" && npm start
