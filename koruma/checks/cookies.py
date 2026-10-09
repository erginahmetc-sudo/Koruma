from __future__ import annotations

from koruma.models import Finding, Severity

NAME = "cookies"
SESSION_HINTS = ("sess", "sid", "auth", "token", "jwt", "login", "remember")


def _parse_set_cookie(raw_headers) -> list[tuple[str, dict]]:
    cookies = []
    for value in raw_headers:
        parts = [p.strip() for p in value.split(";")]
        if not parts or "=" not in parts[0]:
            continue
        name = parts[0].split("=", 1)[0]
        attrs = {}
        for p in parts[1:]:
            k, _, v = p.partition("=")
            attrs[k.lower()] = v
        cookies.append((name, attrs))
    return cookies


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[str] = set()
    https = ctx.base_url.startswith("https://")
    for page in ctx.crawl.pages[:10]:
        resp = ctx.client.get(page.url, allow_redirects=False)
        if resp is None:
            continue
        raw = resp.raw.headers.getlist("Set-Cookie") if hasattr(resp.raw.headers, "getlist") else []
        for name, attrs in _parse_set_cookie(raw):
            if name in seen:
                continue
            seen.add(name)
            sensitive = any(h in name.lower() for h in SESSION_HINTS)
            bump = Severity.MEDIUM if sensitive else Severity.LOW
            if https and "secure" not in attrs:
                findings.append(Finding(NAME, f"Çerezde Secure bayrağı yok: {name}", bump, page.url,
                                        "Çerez şifresiz HTTP bağlantısı üzerinden de gönderilebilir.",
                                        "Çereze Secure bayrağını ekleyin."))
            if "httponly" not in attrs:
                findings.append(Finding(NAME, f"Çerezde HttpOnly bayrağı yok: {name}", bump, page.url,
                                        "JavaScript (ve dolayısıyla bir XSS) çereze erişebilir.",
                                        "Oturum çerezlerine HttpOnly bayrağını ekleyin."))
            # Çerez önekleri (__Secure- / __Host-) ek güvenlik sağlar
            if name.startswith("__Host-"):
                if "secure" not in attrs or attrs.get("path") != "/" or "domain" in attrs:
                    findings.append(Finding(NAME, f"__Host- öneki kuralları ihlal ediliyor: {name}", Severity.LOW, page.url,
                                            "__Host- önekli çerez Secure olmalı, Path=/ taşımalı ve Domain içermemelidir.",
                                            "Çerezi Secure; Path=/ ile ve Domain özniteliği olmadan ayarlayın."))
            elif name.startswith("__Secure-") and "secure" not in attrs:
                findings.append(Finding(NAME, f"__Secure- öneki kuralı ihlal ediliyor: {name}", Severity.LOW, page.url,
                                        "__Secure- önekli çerez Secure bayrağı taşımalıdır.",
                                        "Çereze Secure bayrağını ekleyin."))
            elif sensitive and https and not name.startswith(("__Host-", "__Secure-")):
                findings.append(Finding(NAME, f"Oturum çerezinde güvenlik öneki yok: {name}", Severity.INFO, page.url,
                                        "__Host- veya __Secure- öneki, çerezin yalnızca HTTPS üzerinden ve doğru "
                                        "kapsamda ayarlanmasını tarayıcı düzeyinde zorlar.",
                                        "Oturum çerezini __Host- önekiyle adlandırmayı değerlendirin."))

            samesite = attrs.get("samesite", "").lower()
            if not samesite:
                findings.append(Finding(NAME, f"Çerezde SameSite özniteliği yok: {name}", Severity.LOW, page.url,
                                        "CSRF saldırılarına karşı koruma zayıflar.",
                                        "SameSite=Lax veya SameSite=Strict ayarlayın."))
            elif samesite == "none" and "secure" not in attrs:
                findings.append(Finding(NAME, f"SameSite=None ama Secure yok: {name}", Severity.LOW, page.url,
                                        "Modern tarayıcılar bu çerezi reddeder.", "Secure bayrağını ekleyin."))
    return findings
