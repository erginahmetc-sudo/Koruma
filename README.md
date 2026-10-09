# Koruma 🛡️

**Kendi web sitenizdeki** yaygın güvenlik açıklarını bulan, yıkıcı olmayan (non-destructive) bir tarama aracı.

Koruma sitenizi gezer (crawl eder), formları ve bağlantıları keşfeder ve bir dizi
güvenlik kontrolü uygular. Çıktı; her bulgu için **sorunu**, **neden önemli
olduğunu** ve **nasıl düzeltileceğini** açıklayan Türkçe bir rapordur.

> ⚠️ **Yalnızca sahibi olduğunuz ya da test etmek için açık izniniz olan siteleri tarayın.**
> İzinsiz güvenlik taraması birçok ülkede suçtur. Araç her çalıştığında bunu onaylatır.

## Neleri kontrol eder?

| Kontrol | Aradığı şeyler |
|---|---|
| `headers` | Eksik güvenlik başlıkları (CSP, X-Frame-Options, …), zayıf CSP, sürüm sızıntısı |
| `tls` | HTTPS yok, HTTP→HTTPS yönlendirmesi, HSTS, sertifika süresi, eski TLS 1.0/1.1 |
| `cookies` | `Secure`, `HttpOnly`, `SameSite` bayrakları eksik çerezler |
| `files` | Açıkta kalan `.git`, `.env`, yedekler, veritabanı dökümleri, dizin listeleme, `phpinfo` vb. |
| `cors` | Aşırı gevşek CORS (origin yansıtma, `null`, credentials ile `*`) |
| `methods` | Riskli HTTP metotları, etkin `TRACE` |
| `disclosure` | Sayfalarda sızan API anahtarları, yığın izleri (stack trace), iç IP'ler, riskli HTML yorumları, karışık içerik |
| `injection` | Yansıtılan XSS, hata tabanlı SQL enjeksiyonu, şablon enjeksiyonu (SSTI), dizin geçişi (path traversal), eksik CSRF token'ı |
| `redirect` | Açık yönlendirme (open redirect) |

Tüm testler **yıkıcı değildir**: hiçbir veriyi silmez/değiştirmez, yalnızca
sunucunun yanıtını okur. Varsayılan olarak `logout`, `delete`, `sil` gibi
bağlantılara girilmez ve POST formları yalnızca `--test-post-forms` ile test edilir.

## Kurulum

```bash
git clone <depo-adresi>
cd Koruma
pip install -e .
# veya sadece bağımlılıklar:
pip install -r requirements.txt
```

## Kullanım

```bash
# En basit hali (onay sorar)
koruma https://siteniz.com

# veya paket olarak
python -m koruma https://siteniz.com

# HTML rapor dosyasına yaz
koruma https://siteniz.com --format html -o rapor.html

# Sadece belirli kontroller
koruma https://siteniz.com --checks headers,tls,cookies

# Giriş yapılmış alanları tara (oturum çerezi vererek)
koruma https://siteniz.com --cookie "session=abc123"

# CI için: ORTA ve üzeri bulgu varsa çıkış kodu 2
koruma https://siteniz.com -y -q --fail-on medium
```

### Önemli seçenekler

| Seçenek | Açıklama |
|---|---|
| `--checks` | Çalıştırılacak kontroller (virgülle) |
| `--max-pages N` | Azami taranacak sayfa (vars. 50) |
| `--delay S` | İstekler arası bekleme (vars. 0.2 sn) — sunucuyu yormamak için |
| `--format text\|json\|html` | Rapor biçimi |
| `-o DOSYA` | Raporu dosyaya yaz |
| `--header "Ad: Değer"` | Ek istek başlığı (örn. `Authorization`) |
| `--cookie "ad=değer"` | Oturum çerezi |
| `--test-post-forms` | POST formlarını da test et (dikkat: yan etkisi olabilir) |
| `--insecure` | TLS doğrulamasını atla |
| `--fail-on SEVIYE` | CI için çıkış kodu (`low`…`critical`) |
| `-y` | Yetki onayını otomatik kabul et |
| `-q` | Sessiz mod |

## Çıkış kodları

- `0` — başarı (ya da `--fail-on` eşiğinin altında bulgular)
- `1` — kullanım/girdi hatası veya onay verilmedi
- `2` — `--fail-on` eşiği veya üzerinde en az bir bulgu

## Geliştirme ve test

```bash
pip install -e ".[dev]"
pytest
```

Testler, `tests/vulnerable_app.py` içindeki kasıtlı olarak açık içeren küçük
bir yerel uygulamaya karşı tüm kontrolleri doğrular. Bu uygulamayı gerçek bir
ortamda çalıştırmayın.

Yeni kontrol eklemek için `koruma/checks/` altına bir modül ekleyip içinde
`NAME` ve `run(ctx) -> list[Finding]` tanımlayın, sonra
`koruma/checks/__init__.py` içindeki `ALL_CHECKS`'e kaydedin.

## Sorumluluk reddi

Koruma bir yardımcı araçtır; **güvenlik garantisi değildir**. Hiçbir otomatik
tarayıcı tüm açıkları bulamaz. Önemli sistemler için profesyonel bir sızma testi
(penetration test) yaptırın.

## Lisans

MIT
