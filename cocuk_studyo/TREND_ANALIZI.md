# Trend analizi → özgün senaryolar

> Bu dosya, en çok izlenen çocuk videolarının **biçim ilkelerini** özetler ve bunların bu projede nasıl **özgün** karakter/senaryo/şarkıya dönüştüğünü gösterir.
> Hiçbir mevcut video, karakter, şarkı sözü, melodi veya senaryo kopyalanmadı ya da yeniden çizilmedi.

## 1. Araştırma bulguları
Bir haber derlemesine göre (Statista listesi, Şubat 2023 verisi; **güncel olmayabilir**):

| Video (kanal) | İzlenme | Biçim |
|---|---|---|
| Baby Shark Dance (Pinkfong) | ~12,3 milyar | 1 dk 21 sn'lik kısa, tekrarlı dans şarkısı |
| Johny Johny Yes Papa (LooLoo Kids) | ~6,59 milyar | tekrarlı ninni/tekerleme |
| Bath Song (Cocomelon) | ~5,96 milyar | günlük rutin şarkısı |
| Phonics Song with Two Words (ChuChu TV) | ~5,12 milyar | harf/ses öğreten şarkı |
| Wheels on the Bus (Cocomelon) | ~4,84 milyar | taşıt + tekerleme |
| Masha ve Koca Ayı | ~4,36 milyar (2020) | karakter odaklı kısa hikâyeler |

Türkiye'de en çok izlenen kanallar arasında Sevimli Dostlar (~16,85 milyar toplam izlenme, Şubat 2026 verisi), Oyuncak Oynuyorum ve Maşa ile Koca Ayı geliyor. Renk öğreten tek bir videonun 3 milyar üstü izlenmesi de "renk + nesne" biçiminin gücünü gösteriyor.
Kaynaklarda ortak vurgu: **kısa ve tekrarlı, akılda kalıcı, parlak görsel, temel kavramlar (renk/sayı/hayvan/harf), çocukların aynı şeyi tekrar tekrar izlemesi**.

## 2. Biçim ilkeleri → özgün dönüşüm

| Popüler biçim ilkesi | Bu projedeki özgün karşılığı |
|---|---|
| Kısa, tekrarlı dans şarkısı | Her bölümde **"dans bloğu"**: 2 sn'lik söz parçaları, müzik temposuna kilitli zıplama. Sözler tamamen özgün ("Işıl ışıl yıldızlar!", "Say say say say!", "Hep beraber söyle!") |
| Tekerleme + taşıt | **Yardımcı Araçlar** bölümü: her araç bir görev üstlenir, sesini çıkarır, teşekkür alır. Özgün hikâye, özgün sözler |
| Günlük rutin şarkısı | **Güzel Bir Gün**: el yıkama (5 köpük sayma), diş fırçalama (10 sayma), kahvaltı, oyuncak toplama, banyo, uyku |
| Harf/ses/kavram öğreten şarkı | Sayma (1–20, geri sayım), renkler + karışım, şekiller, **zıt kelimeler**, duygular — hepsi **TR→EN çift dilli**, her kelime 3 farklı bağlamda tekrarlanır |
| Karakter odaklı seri | **Pofi ve Dostları (Baloncuk Vadisi)** – 6 özgün karakter: Pofi, Mimi, Dodo, Zuzu, Bobo, Luna. Her biri farklı renk, kulak/anten, aksesuar ve **ayrı ses** |
| Sürpriz/renk açılımı | **Sihirli Fırça** bölümü: fırça dokunur, renk ve nesne belirir |
| Hikâyeli ders | **Kayıp Yıldızlar**, **Elma Toplama Günü**, **Uçan Balonlar** (sayma macerası); **Paylaşmak Güzel** (6 kurabiyeyi 3 kişiye paylaşma: "iki, iki, iki"); **Duygularımız** (üzgün → sarılma → teşekkür) |

## 3. Hız ve görsel kalite (talep: "çok hızlı geçiş, yüksek kalite")
- 1920×1080, 30 fps, tamamı vektör çizim (anti-alias, degrade, gölge, parlama).
- Ortalama çekim süresi ≈ 1,8 sn, **hiçbir çekim 2 sn'yi geçmez** (yaklaşık 500 çekim / video).
- Her çekimde farklı arka plan (9 tema), kamera zoom/kayma, karakter hareketi, dudak senkronu.
- Geçiş yumuşak "iris" açılışıdır; **beyaz parlama yoktur** (nöbet/parlama güvenliği).

## 4. YouTube Kids uyumu
Araştırmada doğrulanan noktalar ([resmi politika sayfası](https://support.google.com/youtubekids/answer/10938174)): içerik yaşa uygun olmalı ve kalite ilkelerine uymalı; "çocuklara özel" işaretini içerik sahibi koyar; çocuklara özel videolarda kişiselleştirilmiş reklam, yorum ve bildirim yoktur. Şiddet/korkutucu içeriğin dışlandığı bilgisi ikincil bir kaynaktan ([AIR Media-Tech](https://air.io/en/youtube-hacks/how-to-ensure-your-youtube-kids-content-stays-within-youtubes-community-guidelines)). **Parlama kuralları için resmî kaynak bulamadım**; bu yüzden WCAG/Harding "genel parlama" ölçütüne (1 sn'de ≤3 parlama) göre kendi denetimimizi yazdım.

`guvenlik.py` şunları denetler (rapor: `cikti/<video>/uyum_raporu.md`):
1. Yasaklı sözcük (şiddet, korku, hakaret, alkol/sigara, satış/abone-ol çağrısı), bağlantı/@/#, marka adı
2. Çekim süresi ≤ 2 sn, toplam süre ≥ 15 dk, sesin çekime sığması
3. Çıkış videosunda parlama analizi, çözünürlük ≥ 1080p, ses seviyesi (−23…−12 LUFS) ve tepe ≤ −1 dBFS

## 5. Yayın öncesi önerilerim (otomatik denetimin yerini tutmaz)
- Yüklerken **"Çocuklara özel"** işaretleyin; açıklamaya bağlantı/çağrı koymayın.
- Ses `espeak-ng` ile üretildi (robotik). Yayından önce insan seslendirmesi veya daha doğal bir TTS ile değiştirmeniz kaliteyi belirgin artırır; YouTube'un güncel "tekrarlı/otomatik üretilmiş içerik" ve "yapay içerik bildirimi" kurallarını yayından önce kendiniz kontrol edin.
- Emoji grafikleri Twemoji (CC-BY 4.0): açıklamaya "Emoji graphics © Twitter, Inc. and other contributors, CC-BY 4.0" atfı ekleyin.
- Bir çocuk gelişimi uzmanı veya ebeveyn grubuyla kısa bir izleme testi yapın.

## Kaynaklar
- [Baby Shark is the most watched YouTube video in history – top 10](https://www.peterboroughtoday.co.uk/read-this/baby-shark-is-the-most-watched-youtube-video-in-history-heres-the-top-10-3022676)
- [YouTube'da En Çok İzlenen Türk Kanalları (Şubat 2026) – Tamindir](https://www.tamindir.com/haber/youtube-en-cok-izlenen-turk-kanallari-subat-2026_106093/)
- [Content policies for YouTube Kids](https://support.google.com/youtubekids/answer/10938174)
- [YouTube Kids content compliance – AIR Media-Tech](https://air.io/en/youtube-hacks/how-to-ensure-your-youtube-kids-content-stays-within-youtubes-community-guidelines)
