#!/usr/bin/env bash
# Koruma - Kurulum betiği (Linux / macOS)
# Kullanım: ./setup.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗ HATA:${NC} $1"; exit 1; }
step() { echo -e "\n${CYAN}$1${NC}"; }

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║        KORUMA - Kurulum Sihirbazı         ║"
echo "  ║   Kendi web sitenizin güvenlik tarayıcısı ║"
echo "  ╚══════════════════════════════════════════╝"

step "[1/5] Python kontrol ediliyor..."
PYCMD=""
for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then PYCMD="$cand"; break; fi
done
[ -n "$PYCMD" ] || fail "Python bulunamadı. https://www.python.org/downloads/ adresinden Python 3.9+ kurun."
ok "Bulundu: $($PYCMD --version) ($PYCMD)"

step "[2/5] Node.js kontrol ediliyor..."
command -v node >/dev/null 2>&1 || fail "Node.js bulunamadı. https://nodejs.org adresinden Node.js 18+ (LTS) kurun."
ok "Bulundu: $(node --version)"

step "[3/5] Python kütüphaneleri kuruluyor (requests, beautifulsoup4, dnspython, reportlab)..."
"$PYCMD" -m pip install --upgrade pip --quiet 2>/dev/null || true
# Sırayla dene: normal -> --user -> --break-system-packages (Debian/Ubuntu'nun
# "externally-managed-environment" kısıtlaması için). Electron aynı sistem
# python3'ünü PATH'ten çağırdığından venv kullanılmaz.
install_ok=0
for extra in "" "--user" "--break-system-packages" "--user --break-system-packages"; do
    if "$PYCMD" -m pip install -e . --quiet $extra 2>/tmp/koruma-pip-err.log; then
        install_ok=1
        break
    fi
done
[ "$install_ok" = "1" ] || { cat /tmp/koruma-pip-err.log >&2; fail "Python kütüphaneleri kurulamadı."; }
ok "Tamamlandı."

step "[4/5] Masaüstü uygulaması bağımlılıkları kuruluyor (npm install)..."
echo "  Bu işlem birkaç dakika sürebilir, lütfen bekleyin..."
(cd "$ROOT/desktop" && npm install --no-fund --no-audit --loglevel=error) || fail "npm install başarısız oldu."
ok "Tamamlandı."

step "[5/5] Masaüstü arayüzü derleniyor..."
(cd "$ROOT/desktop" && npm run build:ui --silent)
ok "Tamamlandı."

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║           KURULUM TAMAMLANDI!             ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""
echo "  Koruma'yı şu şekilde çalıştırabilirsiniz:"
echo ""
echo "    1) Masaüstü uygulaması : ./baslat.sh"
echo "       (veya desktop klasöründe: npm start)"
echo ""
echo "    2) Komut satırından    : koruma https://siteniz.com"
echo ""
echo "    3) Linux AppImage      : desktop klasöründe 'npm run dist:linux'"
echo ""

read -r -p "Şimdi masaüstü uygulamasını başlatmak ister misiniz? [E/h] " LAUNCH
LAUNCH=${LAUNCH:-E}
if [[ "$LAUNCH" =~ ^[EeYy]$ ]]; then
    (cd "$ROOT/desktop" && npm start)
fi
