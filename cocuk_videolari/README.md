# Çocuk Videoları (TR + EN) – YouTube Kids uyumlu, 3 × 10 dk

Üç eğitici video; her biri **300 sahne × 2,0 sn = 10:00 dk**, 1280×720, 20 fps, hiçbir sahne 2 saniyeyi aşmaz.
Her sahnede ekranda Türkçe (üst bant) ve İngilizce (alt bant) yazı, sesli olarak önce Türkçe sonra İngilizce söylenir.

| # | Dosya | Konu |
|---|-------|------|
| 1 | `cikti/1_renkler-ve-sayilar.mp4` | 1–20 sayma, onlar, sıra sayıları, geri sayım, 11 renk × 4 nesne, gökkuşağı |
| 2 | `cikti/2_hayvanlar-ve-sesleri.mp4` | 60+ hayvan adı ve ~20 hayvan sesi (çiftlik, vahşi, deniz, kuş/böcek) |
| 3 | `cikti/3_sekiller-meyveler-tasitlar.mp4` | 11 şekil, meyve, sebze, taşıt, vücut, doğa, duygular, yiyecekler |

Kapak görselleri: `cikti/*_kapak.jpg`. Sahne sahne senaryo/zamanlama: `cikti/*_senaryo.json`.

## Trend araştırmasından çıkan formül
- En çok izlenen çocuk kanalları (Cocomelon, Pinkfong, ChuChu TV, Blippi, Ms. Rachel; Türkiye'de Sevimli Dostlar, Maşa ile Koca Ayı) **renk, sayı, hayvan, şekil** gibi temel kavramları, canlı renkler ve tekrarla öğretiyor.
- Ek olarak Türkiye'de renk öğreten tek bir videonun 3 milyar üstü izlenmesi, "renk + nesne" formatının gücünü gösteriyor.
- Bu yüzden her video: parlak renkler, dönen ışın arka planı, her yarım saniyede (120 BPM) bir zıplama, konfeti, **tekrar eden turlar** (aynı kelime farklı animasyonla 3 kez), çift dilli kısa kelimeler.

## YouTube Kids'e yükleme önerileri
- Yüklerken **"Çocuklara özel"** seçeneğini işaretleyin (zorunlu); yorumlar/kişiselleştirilmiş reklam otomatik kapanır.
- İçerikte şiddet, marka, reklam, korkutucu öğe, harici bağlantı yoktur; emoji grafikleri Twemoji (CC-BY 4.0, atıf: "Graphics © Twitter/X Corp, CC-BY 4.0") ve müzik/ses programatik üretilmiştir.
- Öneri başlıklar `icerik.py` içindedir (`title_tr`, `title_en`, `tags`).
- Hızlı ışık/yanıp sönme: sahne geçişinde 0,1 sn'lik yumuşak beyaz parlama vardır; isterseniz `uret.py` içindeki `if t < 0.1` satırını silerek kapatabilirsiniz.

## Yeniden üretmek
```bash
sudo apt-get install -y espeak-ng ffmpeg
pip install pillow numpy cairosvg
cd cocuk_videolari && npm install        # Twemoji SVG'leri
python3 uret.py 1      # veya 2, 3   (her biri ~5-6 dk sürer)
python3 uret.py 1 --test 6   # sadece ilk 6 sahne
```
Sesler `espeak-ng` ile üretildiği için robotiktir. Daha doğal ses için `icerik.py`'deki metinleri bir TTS/seslendirme ile üretip `uret.py` içindeki `voice()` fonksiyonunu değiştirmek yeterlidir.
