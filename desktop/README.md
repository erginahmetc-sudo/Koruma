# Koruma — Masaüstü Uygulaması (Electron + React)

Kendi web sitenizdeki güvenlik açıklarını, **tek bir pencereden** bulmanızı
sağlayan Windows/Linux masaüstü uygulaması. Arayüz **React**, kabuk **Electron**,
tarama motoru ise bu depodaki **Python `koruma` paketidir**.

![Arayüz](../scanner-ui.png)

## Nasıl çalışır?

1. Arayüze sitenizin adresini yazar, "sahibiyim/iznim var" kutusunu işaretler ve
   **Açıkları Tara**'ya tıklarsınız.
2. Electron ana süreci, Python motorunu
   `python -m koruma <url> --progress-json --format json` olarak çalıştırır.
3. İlerleme canlı olarak akar; bitince bulgular önem düzeyine göre renkli
   kartlar halinde listelenir. Raporu HTML veya JSON olarak kaydedebilirsiniz.

Tüm tarama **yıkıcı değildir** ve yalnızca sizin girdiğiniz sitenin host'una
istek atar (bkz. ana depodaki `README.md`).

## Gereksinimler

- **Node.js 18+** (geliştirme/paketleme için)
- **Python 3.9+** — uygulama çalışırken motoru çağırmak için gereklidir.
  Python'ın `requests` ve `beautifulsoup4` paketleri kurulu olmalıdır:
  ```bash
  pip install requests beautifulsoup4
  ```
  > Uygulama, `py`, `python` ve `python3` komutlarını sırayla dener. Farklı bir
  > yorumlayıcı için `KORUMA_PYTHON` ortam değişkenini ayarlayabilirsiniz.

## Geliştirme

```bash
cd desktop
npm install
npm run dev      # Vite + Electron canlı yeniden yükleme ile
```

Tek seferlik çalıştırma (arayüzü derleyip Electron'u açar):

```bash
npm run start
```

## Windows kurulum paketi (.exe) oluşturma

**Bir Windows makinesinde** (veya Wine kurulu bir ortamda):

```bash
cd desktop
npm install
npm run dist:win
```

Çıktı: `desktop/release/Koruma-Setup-0.1.0.exe` (NSIS kurulumu, Türkçe).

> Not: Windows `.exe`'si yalnızca Windows'ta (veya Wine ile) üretilebilir.
> Linux `AppImage` için `npm run dist:linux`, paketlemeyi test etmek için
> `npm run dist:dir` kullanın.

## Uçtan uca duman testi

Gerçek motoru, yerel zafiyetli test uygulamasına karşı çalıştırıp JSON çıktısını
ve ilerleme akışını doğrular (pencere açmadan):

```bash
node e2e-smoke.js
```

## Mimari

```
desktop/
├── electron/
│   ├── main.js      # Pencere + Python motorunu spawn etme, IPC, rapor kaydetme
│   └── preload.js   # Güvenli köprü (contextIsolation açık)
├── src/             # React arayüzü
│   ├── App.jsx      # Ana ekran, durum yönetimi
│   ├── components/  # FindingCard, SummaryBar
│   ├── constants.js # Kontroller ve önem düzeyleri
│   └── report.js    # HTML rapor üretimi
└── build/           # Uygulama ikonları
```

Motor (`../koruma`), paketlemede `resources/engine/koruma` altına kopyalanır ve
`PYTHONPATH` buna ayarlanır.

## Güvenlik notları

- `contextIsolation: true`, `nodeIntegration: false` — renderer'a yalnızca
  `preload.js` üzerinden sınırlı API açılır.
- Arayüzde CSP uygulanır; harici bağlantılar sistem tarayıcısında açılır.
- Uygulama her taramadan önce yetki onayı ister.
