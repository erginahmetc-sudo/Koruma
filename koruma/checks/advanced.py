"""Gelişmiş, yıkıcı olmayan kontroller: CRLF enjeksiyonu, Host başlığı
enjeksiyonu ve hassas sayfalarda önbellekleme (cache) politikası.

Hiçbiri veri değiştirmez; yalnızca sunucunun girdileri ve başlıkları nasıl
işlediğini gözlemler.
"""
from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from koruma.models import Finding, Severity

NAME = "advanced"
CRLF_HEADER = "X-Koruma-Crlf"
EVIL_HOST = "koruma-host-testi.example"


def _check_crlf(ctx) -> list[Finding]:
    findings = []
    reported = set()
    for url in ctx.crawl.param_urls[:15]:
        p = urlparse(url)
        params = dict(parse_qsl(p.query, keep_blank_values=True))
        for name in params:
            if name in reported:
                continue
            # URL'ye doğrudan kodlanmış CRLF yerleştir (çift kodlamadan kaçın)
            payload = f"koruma%0d%0a{CRLF_HEADER}%3A%20enjekte"
            others = "&".join(f"{k}={v}" for k, v in params.items() if k != name)
            query = f"{name}={payload}" + (("&" + others) if others else "")
            target = urlunparse(p._replace(query=query))
            r = ctx.client.get(target, allow_redirects=False)
            if r is None:
                continue
            if any(h.lower() == CRLF_HEADER.lower() for h in r.headers):
                reported.add(name)
                findings.append(Finding(NAME, f"CRLF enjeksiyonu / HTTP yanıt bölme: '{name}'", Severity.HIGH, url,
                    "Girdiye yerleştirilen satır sonu karakterleri (CR/LF) yanıt başlıklarına yeni bir "
                    "başlık enjekte etti. Bu, başlık/çerez enjeksiyonu ve önbellek zehirlenmesine yol açabilir.",
                    "Girdideki satır sonu karakterlerini (\\r \\n) başlıklara yazmadan önce temizleyin/reddedin.",
                    f"{name}=…%0d%0a{CRLF_HEADER}: … -> yanıtta {CRLF_HEADER} başlığı belirdi"))
    return findings


def _check_host_header(ctx) -> list[Finding]:
    findings = []
    base = ctx.base_url
    host = urlparse(base).hostname
    for header in ("Host", "X-Forwarded-Host"):
        r = ctx.client.get(base, headers={header: EVIL_HOST}, allow_redirects=False)
        if r is None:
            continue
        loc = r.headers.get("Location", "")
        body = r.text if "html" in r.headers.get("Content-Type", "") else ""
        if EVIL_HOST in loc or (body and EVIL_HOST in body):
            where = "Location başlığı" if EVIL_HOST in loc else "sayfa içeriği"
            findings.append(Finding(NAME, f"Host başlığı enjeksiyonu ({header})", Severity.MEDIUM, base,
                f"Sahte {header} başlığı {where}'nde yansıtıldı. Saldırgan, parola sıfırlama bağlantıları "
                "gibi üretilen mutlak URL'leri kendi alan adına yönlendirebilir (örn. parola sıfırlama zehirlenmesi).",
                "Üretilen bağlantılarda Host başlığına güvenmeyin; sabit, yapılandırılmış bir alan adı kullanın "
                "ve bilinen host'ları beyaz listeye alın.",
                f"{header}: {EVIL_HOST} -> {where}"))
            break
    return findings


def _check_cache(ctx) -> list[Finding]:
    findings = []
    reported = set()
    for page in ctx.crawl.pages[:15]:
        resp = ctx.client.get(page.url, allow_redirects=False)
        if resp is None:
            continue
        sets_session = any("set-cookie" == k.lower() and
                           any(h in v.lower() for h in ("sess", "token", "auth", "sid"))
                           for k, v in resp.headers.items())
        has_pw = page.body and ('type="password"' in page.body or "type='password'" in page.body)
        if not (sets_session or has_pw):
            continue
        cc = resp.headers.get("Cache-Control", "").lower()
        if page.url in reported:
            continue
        if not cc or ("no-store" not in cc and "private" not in cc and "no-cache" not in cc):
            reported.add(page.url)
            findings.append(Finding(NAME, "Hassas sayfada önbellekleme kısıtlanmamış", Severity.LOW, page.url,
                "Oturum çerezi belirleyen veya parola formu içeren bu sayfa için Cache-Control "
                "no-store/private ayarlanmamış; ortak/ara önbellekler hassas içeriği saklayabilir.",
                "Hassas yanıtlara 'Cache-Control: no-store' (veya en az private, no-cache) ekleyin.",
                f"Cache-Control: {cc or '(yok)'}"))
    return findings


def run(ctx) -> list[Finding]:
    findings = []
    findings += _check_crlf(ctx)
    findings += _check_host_header(ctx)
    findings += _check_cache(ctx)
    return findings
