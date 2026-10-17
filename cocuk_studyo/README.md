# Çocuk Stüdyosu – "Pofi ve Dostları" (TR + EN, ≥ 15 dk, YouTube Kids uyumlu)

Özgün karakterlerle, otomatik üretilen yüksek kaliteli (1080p30) eğitici çocuk videoları.
Trend araştırması ve özgünleştirme mantığı: [`TREND_ANALIZI.md`](TREND_ANALIZI.md).

## Videolar (her biri ≥ 15:00, ~500 çekim, çekim ≤ 2 sn)
| # | Başlık | Bölümler |
|---|--------|----------|
| 1 | Pofi ve Dostları: Say, Boya, Öğren! | Kayıp Yıldızlar (sayma 1–20) · Sihirli Fırça (renkler) · Çiftlik Dostları · Şekil Geçit Töreni · Paylaşmak Güzel · Zıt Kelimeler · Güzel Bir Gün · Duygularımız |
| 2 | Pofi ve Dostları: Hayvanlar, Araçlar ve Duygular | Elma Toplama Günü · Yardımcı Araçlar · Vahşi Doğa Dostları · Sihirli Fırça · Duygularımız · Elmaları Paylaşalım · Şekiller · Zıt Kelimeler |
| 3 | Pofi ve Dostları: Güzel Bir Gün | Uçan Balonlar · Güzel Bir Gün · Deniz ve Gökyüzü Dostları · Şekiller · Yardımcı Araçlar · Zıt Kelimeler · Çilekleri Paylaşalım · Sihirli Fırça |

## Kullanım
```bash
sudo apt-get install -y espeak-ng ffmpeg
pip install cairocffi cairosvg pillow numpy
cd cocuk_studyo && npm install @twemoji/svg      # emoji vektörleri (veya ../cocuk_videolari/node_modules kullanılır)

python3 studyo.py uret 1            # 1, 2, 3 veya hepsi   (--test 60 : yalnızca ilk 60 çekim)
python3 studyo.py kontrol 1         # uyum raporu → cikti/<video>/uyum_raporu.md
python3 studyo.py onizleme 1        # 480p önizleme
```
Çıktı: `cikti/<video>/<video>.mp4`, `senaryo.json` (çekim çekim metin/zaman), `uyum_raporu.md`.
Render hızı ≈ gerçek süre kadar (4 çekirdekte video başına ~15 dk).

## Mimari
| Dosya | Görev |
|---|---|
| `karakter.py` | 6 özgün karakter (cairo vektör): gövde, kulak/anten, aksesuar, yüz ifadeleri, göz kırpma, **dudak senkronu**, squash-stretch dans |
| `dunya.py` | 9 paralaks arka plan, emoji/şekil rekvizitleri, yazı/alt yazı, parıltılar |
| `sahne.py` | Tek çekimin kamera hareketi, sayma ızgarası, numara rozeti, iris geçişi |
| `hikaye.py` + `icerik_ortak.py` | `Maker` (çekim üretici) ve 9 bölüm şablonu; TR+EN kısa metinler |
| `videolar.py` | 3 videonun kurgusu, tempo/anahtar atamaları, tekrar kuşağı (≥ 15 dk'ya tamamlar) |
| `ses.py` | Karakter başına ayrı espeak-ng sesi, ses zarfı (dudak), sentezlenmiş müzik + efekt, ducking |
| `guvenlik.py` | Senaryo ve medya uyum denetimi (parlama, ses seviyesi, yasaklı sözcük…) |
| `studyo.py` | Paralel render (12 parça × 4 işçi) → birleştir → loudnorm ile ses |

## Yeni bölüm / video eklemek
`hikaye.py` içinde `ep_xxx(m, ...)` yazın (`m.add`, `m.count`, `m.dance`, `m.react` yardımcıları), `videolar.py`'de `SPECS` listesine ekleyin.
Sözleri kısa tutun (≈ 3–4 sözcük): önce Türkçe, sonra İngilizce, toplam ≤ 1,7 sn.

## Sınırlar (dürüst notlar)
- Seslendirme `espeak-ng` olduğundan robotiktir; yayın için insan/gelişmiş TTS önerilir (`ses.voice_for` değiştirilerek takılır).
- Müzik algoritmik üretimdir; basit ama telif sorunu yoktur.
- Parlama denetimi yaklaşık bir ölçümdür (ortalama parlaklık tabanlı); resmî bir sertifika değildir.
