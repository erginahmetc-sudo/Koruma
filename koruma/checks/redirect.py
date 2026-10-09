from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from koruma.models import Finding, Severity

NAME = "redirect"
# Yönlendirme hedefi taşıması muhtemel parametre adları.
REDIRECT_PARAMS = ("next", "url", "redirect", "redirect_uri", "redirect_url", "return", "returnurl",
                   "return_url", "returnto", "dest", "destination", "continue", "goto", "target", "to", "r", "u")
EVIL = "koruma-acik-yonlendirme.example"


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    reported: set = set()

    for url in ctx.crawl.param_urls:
        p = urlparse(url)
        params = dict(parse_qsl(p.query, keep_blank_values=True))
        for name in params:
            if name.lower() not in REDIRECT_PARAMS:
                continue
            if name in reported:
                continue
            for payload in (f"https://{EVIL}/", f"//{EVIL}/", f"https:{EVIL}"):
                test = dict(params)
                test[name] = payload
                target = urlunparse(p._replace(query=urlencode(test)))
                r = ctx.client.get(target, allow_redirects=False)
                if r is None or not (300 <= r.status_code < 400):
                    continue
                loc = r.headers.get("Location", "")
                if urlparse(loc if "//" in loc else "//" + loc.lstrip("/")).hostname == EVIL:
                    reported.add(name)
                    findings.append(Finding(NAME, f"Açık yönlendirme (open redirect): '{name}' parametresi",
                                            Severity.MEDIUM, url,
                                            "Parametreye yazılan harici adres doğrulanmadan Location başlığına konuyor. "
                                            "Kimlik avı (phishing) bağlantıları sizin alan adınızla başlayıp dış siteye "
                                            "yönlendirebilir.",
                                            "Yönlendirme hedeflerini bir beyaz listeyle sınırlayın veya yalnızca göreli "
                                            "yollara (/ ile başlayan, // olmayan) izin verin.",
                                            f"{name}={payload} -> Location: {loc[:120]}"))
                    break
    return findings
