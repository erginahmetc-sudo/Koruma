from __future__ import annotations

import re

from koruma.models import Finding, Severity

NAME = "headers"

REQUIRED = [
    ("Content-Security-Policy", Severity.MEDIUM,
     "XSS ve veri enjeksiyonu saldırılarına karşı ek bir savunma katmanı sağlar.",
     "Örn: Content-Security-Policy: default-src 'self'; object-src 'none'; frame-ancestors 'self'"),
    ("X-Frame-Options", Severity.MEDIUM,
     "Sayfanın başka sitelerde iframe içine alınmasını engeller (clickjacking).",
     "X-Frame-Options: DENY veya CSP'de frame-ancestors 'self' kullanın."),
    ("X-Content-Type-Options", Severity.LOW,
     "Tarayıcının MIME türünü tahmin etmesini (MIME sniffing) engeller.",
     "X-Content-Type-Options: nosniff ekleyin."),
    ("Referrer-Policy", Severity.LOW,
     "Başka sitelere giden isteklerde URL bilgisinin sızmasını sınırlar.",
     "Referrer-Policy: strict-origin-when-cross-origin ekleyin."),
    ("Permissions-Policy", Severity.INFO,
     "Kamera, mikrofon, konum gibi tarayıcı özelliklerine erişimi kısıtlar.",
     "Örn: Permissions-Policy: camera=(), microphone=(), geolocation=()"),
]

VERSION_RE = re.compile(r"\d+\.\d+")


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    html_pages = [p for p in ctx.crawl.pages if "html" in p.content_type and p.status < 400]
    if not html_pages:
        return findings
    page = html_pages[0]
    h = {k.lower(): v for k, v in page.headers.items()}

    for name, sev, why, fix in REQUIRED:
        if name == "X-Frame-Options" and "frame-ancestors" in h.get("content-security-policy", ""):
            continue
        if name.lower() not in h:
            findings.append(Finding(NAME, f"Eksik güvenlik başlığı: {name}", sev, page.url, why, fix))

    csp = h.get("content-security-policy", "")
    if csp:
        directives = {d.strip().split(" ", 1)[0].lower(): d.strip() for d in csp.split(";") if d.strip()}
        script_src = directives.get("script-src") or directives.get("default-src", "")
        if "'unsafe-inline'" in script_src and "'nonce-" not in script_src and "'strict-dynamic'" not in script_src:
            findings.append(Finding(NAME, "CSP 'unsafe-inline' scriptlere izin veriyor", Severity.LOW, page.url,
                                    "'unsafe-inline' CSP'nin XSS korumasını büyük ölçüde etkisiz kılar.",
                                    "Inline scriptleri nonce/hash ile değiştirin.", csp[:200]))
        if "'unsafe-eval'" in csp:
            findings.append(Finding(NAME, "CSP 'unsafe-eval' içeriyor", Severity.LOW, page.url,
                                    "eval() benzeri dinamik kod çalıştırmaya izin verir.",
                                    "'unsafe-eval' ifadesini kaldırın.", csp[:200]))
        # Joker (wildcard) kaynak
        if "*" in script_src.replace("*.", "").split():
            findings.append(Finding(NAME, "CSP script-src joker (*) içeriyor", Severity.LOW, page.url,
                                    "'*' kaynağı herhangi bir yerden script yüklenmesine izin verir; korumayı zayıflatır.",
                                    "script-src'i belirli, güvendiğiniz kaynaklarla sınırlayın.", script_src[:200]))
        # HTTP (şifresiz) kaynak
        if "http://" in csp:
            findings.append(Finding(NAME, "CSP şifresiz (http:) kaynağa izin veriyor", Severity.LOW, page.url,
                                    "http:// kaynaklar ağdaki saldırganca değiştirilebilir.",
                                    "Yalnızca https:// kaynaklara izin verin.", csp[:200]))
        # Önemli yönergelerin eksikliği
        if "default-src" not in directives and "script-src" not in directives:
            findings.append(Finding(NAME, "CSP'de script-src/default-src yok", Severity.LOW, page.url,
                                    "Bu yönergeler olmadan CSP script yüklemeyi kısıtlamaz.",
                                    "En azından default-src 'self' tanımlayın.", csp[:200]))
        if "object-src" not in directives and "default-src" not in directives:
            findings.append(Finding(NAME, "CSP'de object-src yok", Severity.INFO, page.url,
                                    "object-src 'none' eski eklenti tabanlı saldırıları engeller.",
                                    "object-src 'none' ekleyin.", csp[:200]))
        if "base-uri" not in directives:
            findings.append(Finding(NAME, "CSP'de base-uri yok", Severity.INFO, page.url,
                                    "base-uri olmadan <base> etiketi enjeksiyonu göreli URL'leri kaçırabilir.",
                                    "base-uri 'self' (veya 'none') ekleyin.", csp[:200]))

    for hdr in ("Server", "X-Powered-By", "X-AspNet-Version", "X-AspNetMvc-Version"):
        val = h.get(hdr.lower())
        if val and (hdr != "Server" or VERSION_RE.search(val)):
            findings.append(Finding(NAME, f"Sürüm bilgisi sızıyor: {hdr}", Severity.LOW, page.url,
                                    "Yazılım ve sürüm bilgisi saldırganın bilinen açıkları hedeflemesini kolaylaştırır.",
                                    f"{hdr} başlığını kaldırın veya sürüm numarasını gizleyin.", f"{hdr}: {val}"))
    return findings
