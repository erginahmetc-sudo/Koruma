"""DNS ve e-posta kimlik doğrulama kontrolleri.

Alan adınızın e-posta sahteciliğine (spoofing/phishing) ve sertifika yanlış
verilmesine karşı korunup korunmadığını inceler: SPF, DMARC, DKIM, CAA, DNSSEC.

dnspython kuruluysa tam kontrol yapılır; değilse kontrol atlanır ve bir not
düşülür (pip install dnspython).
"""
from __future__ import annotations

from urllib.parse import urlparse

from koruma.models import Finding, Severity

NAME = "dns_email"
COMMON_DKIM_SELECTORS = ["default", "google", "selector1", "selector2", "k1", "dkim",
                         "mail", "s1", "s2", "mandrill", "mailjet"]


def _registrable(host: str) -> str:
    """Basit kayıt edilebilir alan adı çıkarımı (ör. www.a.example.com -> example.com).

    Çok seviyeli TLD'leri (co.uk gibi) tam çözmez; yaygın durumlar için yeterlidir.
    """
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    two_level = {"co", "com", "org", "net", "gov", "edu", "ac"}
    if parts[-2] in two_level and len(parts) >= 3:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    try:
        import dns.resolver  # type: ignore
        import dns.dnssec  # noqa: F401
    except ImportError:
        findings.append(Finding(
            NAME, "DNS kontrolleri atlandı (dnspython kurulu değil)", Severity.INFO, ctx.base_url,
            "SPF/DMARC/DKIM/CAA/DNSSEC kontrolleri için dnspython gereklidir.",
            "pip install dnspython komutuyla kurun ve taramayı tekrarlayın."))
        return findings

    host = urlparse(ctx.base_url).hostname or ""
    # IP adresi veya localhost için DNS/e-posta kontrolleri anlamsızdır
    if host in ("localhost",) or all(p.isdigit() for p in host.split(".")) or ":" in host:
        return findings
    domain = _registrable(host)
    resolver = dns.resolver.Resolver()
    resolver.timeout = ctx.client.timeout
    resolver.lifetime = ctx.client.timeout * 2

    def txt(name):
        try:
            return ["".join(s.decode() if isinstance(s, bytes) else s for s in r.strings)
                    for r in resolver.resolve(name, "TXT")]
        except Exception:
            return []

    # --- SPF ---
    spf = [t for t in txt(domain) if t.lower().startswith("v=spf1")]
    if not spf:
        findings.append(Finding(NAME, "SPF kaydı yok", Severity.MEDIUM, domain,
            "SPF olmadan saldırganlar alan adınız adına e-posta gönderebilir (spoofing).",
            "Bir TXT kaydı ekleyin: \"v=spf1 include:... -all\" (yetkili sunucularınıza göre)."))
    else:
        rec = spf[0]
        low = rec.lower()
        if "+all" in low:
            findings.append(Finding(NAME, "SPF 'all' mekanizması çok gevşek (+all)", Severity.HIGH, domain,
                "+all her sunucunun sizin adınıza e-posta göndermesine izin verir; SPF'i etkisiz kılar.",
                "'+all' yerine '-all' (katı) veya en azından '~all' kullanın.", rec[:200]))
        elif "~all" not in low and "-all" not in low and "?all" not in low:
            findings.append(Finding(NAME, "SPF 'all' mekanizması eksik", Severity.LOW, domain,
                "Kayıt bir 'all' mekanizmasıyla bitmiyor; yetkisiz göndericiler açıkça reddedilmiyor.",
                "Kaydı '-all' veya '~all' ile sonlandırın.", rec[:200]))
        elif "?all" in low:
            findings.append(Finding(NAME, "SPF nötr politika kullanıyor (?all)", Severity.LOW, domain,
                "?all yetkisiz göndericileri ne reddeder ne işaretler; koruma sağlamaz.",
                "'-all' veya '~all' tercih edin.", rec[:200]))

    # --- DMARC ---
    dmarc = [t for t in txt("_dmarc." + domain) if t.lower().startswith("v=dmarc1")]
    if not dmarc:
        findings.append(Finding(NAME, "DMARC kaydı yok", Severity.MEDIUM, "_dmarc." + domain,
            "DMARC olmadan SPF/DKIM başarısız olduğunda ne yapılacağı tanımsızdır; spoofing kolaylaşır.",
            "Bir TXT kaydı ekleyin: \"v=DMARC1; p=reject; rua=mailto:...\" (önce p=none ile izleyin)."))
    else:
        rec = dmarc[0].lower()
        policy = "none"
        for part in rec.split(";"):
            part = part.strip()
            if part.startswith("p="):
                policy = part[2:].strip()
        if policy == "none":
            findings.append(Finding(NAME, "DMARC politikası uygulanmıyor (p=none)", Severity.LOW, "_dmarc." + domain,
                "p=none yalnızca izleme yapar; sahte e-postalar yine de teslim edilir.",
                "Hazır olduğunuzda p=quarantine, ardından p=reject'e yükseltin.", dmarc[0][:200]))

    # --- DKIM (yaygın seçicileri dene) ---
    found_dkim = [s for s in COMMON_DKIM_SELECTORS
                  if any("v=dkim1" in t.lower() or "p=" in t.lower()
                         for t in txt(f"{s}._domainkey.{domain}"))]
    if not found_dkim:
        findings.append(Finding(NAME, "DKIM kaydı bulunamadı (yaygın seçiciler)", Severity.INFO, domain,
            "Yaygın seçicilerde DKIM anahtarı görülmedi. DKIM, e-postaları imzalayarak sahteciliği zorlaştırır. "
            "(Farklı bir seçici kullanıyor olabilirsiniz.)",
            "E-posta sağlayıcınızın DKIM imzalamasını etkinleştirin."))

    # --- CAA ---
    try:
        caa = list(resolver.resolve(domain, "CAA"))
    except Exception:
        caa = []
    if not caa:
        findings.append(Finding(NAME, "CAA kaydı yok", Severity.LOW, domain,
            "CAA kaydı olmadan herhangi bir sertifika otoritesi alan adınıza sertifika verebilir "
            "(yanlış sertifika verme riski).",
            "Bir CAA kaydı ekleyin, ör. 0 issue \"letsencrypt.org\"."))

    # --- DNSSEC (DNSKEY kaydının varlığı) ---
    try:
        has_dnskey = len(list(resolver.resolve(domain, "DNSKEY"))) > 0
    except Exception:
        has_dnskey = False
    if not has_dnskey:
        findings.append(Finding(NAME, "DNSSEC etkin değil", Severity.INFO, domain,
            "DNSSEC, DNS yanıtlarının kriptografik olarak doğrulanmasını sağlar; DNS sahteciliğini (cache poisoning) zorlaştırır.",
            "Alan adı sağlayıcınızda DNSSEC'i etkinleştirin."))

    return findings
