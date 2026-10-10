"""Teknoloji parmak izi: sunucu, dil, çerçeve ve CMS tespiti.

Tespit edilen yığını (stack) bilgilendirme amaçlı raporlar ve sürüm ifşasını
not düşer. Bu, "güncel olmayan bileşen" (OWASP A06) değerlendirmesine bağlam
sağlar; saldırganlar da ilk iş bu bilgiyi toplar.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from koruma import baseline
from koruma.models import Finding, Severity

NAME = "fingerprint"

COOKIE_TECH = {
    "wordpress_": "WordPress", "wp-settings": "WordPress",
    "phpsessid": "PHP", "laravel_session": "Laravel (PHP)", "xsrf-token": None,
    "ci_session": "CodeIgniter (PHP)", "jsessionid": "Java (JSP/Servlet)",
    "asp.net_sessionid": "ASP.NET", ".aspxauth": "ASP.NET",
    "connect.sid": "Express (Node.js)", "csrftoken": "Django (Python)",
    "sessionid": None, "_django": "Django (Python)", "rack.session": "Ruby (Rack/Rails)",
}

GENERATOR_RX = re.compile(r"(WordPress|Joomla!?|Drupal|Shopify|Wix|Ghost|Hugo|Jekyll|Gatsby|TYPO3|PrestaShop|Magento)\s*([0-9][0-9.]*)?", re.I)

PATH_TECH = [
    ("/wp-login.php", "WordPress yönetim girişi"),
    ("/administrator/", "Joomla yönetim paneli"),
    ("/user/login", "Drupal giriş"),
    ("/.well-known/apple-app-site-association", None),
]


def _server_stack(headers: dict) -> list[tuple[str, str]]:
    h = {k.lower(): v for k, v in headers.items()}
    found = []
    for key, label in (("server", "Sunucu"), ("x-powered-by", "Çalıştıran"),
                       ("x-aspnet-version", "ASP.NET"), ("x-generator", "Üretici"),
                       ("x-drupal-cache", "Drupal"), ("x-redirect-by", "Yönlendirme")):
        if key in h and h[key]:
            found.append((label, h[key]))
    return found


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    detected: dict[str, str] = {}  # teknoloji -> kanıt

    html_pages = [p for p in ctx.crawl.pages if "html" in p.content_type and p.status < 400]
    home = html_pages[0] if html_pages else (ctx.crawl.pages[0] if ctx.crawl.pages else None)
    if home is None:
        return findings

    # 1) Yanıt başlıkları
    for label, val in _server_stack(home.headers):
        detected[f"{label}: {val}"] = f"HTTP başlığı"

    # 2) <meta name="generator">
    if home.body:
        soup = BeautifulSoup(home.body, "html.parser")
        gen = soup.find("meta", attrs={"name": re.compile("generator", re.I)})
        if gen and gen.get("content"):
            content = gen["content"]
            m = GENERATOR_RX.search(content)
            detected[content.strip()] = "meta generator"
            if m and m.group(2):
                findings.append(Finding(
                    NAME, f"CMS sürümü ifşa ediliyor: {m.group(1)} {m.group(2)}", Severity.LOW, home.url,
                    "Sayfa kaynağı, kullanılan CMS'in tam sürümünü açık ediyor; bu, o sürüme ait "
                    "bilinen açıkların doğrudan hedeflenmesini kolaylaştırır.",
                    "<meta name=\"generator\"> etiketini kaldırın ve CMS'i güncel tutun.",
                    content.strip()))
        # WordPress belirtileri
        if re.search(r"/wp-content/|/wp-includes/", home.body):
            detected.setdefault("WordPress", "wp-content/wp-includes yolları")

    # 3) Çerezlerden teknoloji
    resp = ctx.client.get(home.url, allow_redirects=False)
    if resp is not None:
        for c in resp.cookies:
            low = c.name.lower()
            for hint, tech in COOKIE_TECH.items():
                if tech and hint in low:
                    detected.setdefault(tech, f"çerez: {c.name}")

    # 4) Birkaç belirleyici yol
    from urllib.parse import urljoin
    bl = baseline.get(ctx)
    for path, label in PATH_TECH:
        if label is None:
            continue
        r = ctx.client.get(urljoin(ctx.base_url, path), allow_redirects=False)
        if r is not None and r.status_code in (200, 301, 302, 403) and not bl.matches_response(r):
            detected.setdefault(label, f"{path} ({r.status_code})")

    if detected:
        evidence = "; ".join(f"{k} [{v}]" for k, v in list(detected.items())[:12])
        findings.append(Finding(
            NAME, f"Tespit edilen teknolojiler ({len(detected)})", Severity.INFO, home.url,
            "Sitede kullanılan sunucu/çerçeve/CMS bileşenleri tespit edildi. Bu bilgi tek başına "
            "bir açık değildir ancak bu bileşenlerin güncel tutulması gerekir (OWASP A06).",
            "Bileşenleri güncel tutun, gereksiz sürüm/teknoloji ifşasını kapatın.",
            evidence))
    return findings
