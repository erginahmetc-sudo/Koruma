"""OWASP A01:2021 — Bozuk Erişim Kontrolü (Broken Access Control).

Üç yıkıcı olmayan teknik uygular:
  1. Forced browsing — hassas/yönetim yollarının kimlik doğrulaması olmadan
     erişilebilir olup olmadığı.
  2. IDOR heuristiği — sıralı/numeric kimliklerin numaralandırılabilirliği.
  3. Kimlik doğrulamalı vs doğrulamasız karşılaştırma — kullanıcı oturum
     çerezi verdiyse, korunması gereken sayfaların oturumsuz da aynı içeriği
     döndürüp döndürmediği.

Not: Otomatik bir araç bir isteğin BAŞARILI olduğunu görebilir ama o verinin
görülmeye YETKİLİ olup olmadığını kesin bilemez; bu yüzden IDOR bulguları
"olası" olarak, düşük/orta güvenle raporlanır.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from koruma.models import Finding, Severity

NAME = "access"

# Kimlik doğrulaması beklenen, oturumsuz erişilebilir olmaması gereken yollar
PROTECTED_PATHS = [
    ("admin/", "Yönetim paneli"),
    ("admin/index.php", "Yönetim paneli"),
    ("dashboard", "Kontrol paneli"),
    ("account", "Hesap sayfası"),
    ("settings", "Ayarlar"),
    ("user/profile", "Kullanıcı profili"),
    ("api/admin", "Yönetim API'si"),
    ("admin/users", "Kullanıcı yönetimi"),
]

ERROR_HINTS = ("not found", "bulunamadı", "error", "hata", "forbidden", "yasak", "denied",
               "login", "giriş", "oturum", "sign in", "unauthorized")


def _looks_like_record(resp) -> bool:
    """Yanıt, hata/giriş sayfası değil de gerçek bir içerik gibi mi görünüyor?"""
    if resp is None or resp.status_code != 200:
        return False
    body = resp.text or ""
    if len(body) < 50:
        return False
    low = body[:600].lower()
    if any(h in low for h in ("login", "giriş yap", "sign in", "unauthorized", "403 forbidden")):
        return False
    return True


def _numeric_params(url: str):
    p = urlparse(url)
    params = dict(parse_qsl(p.query, keep_blank_values=True))
    return p, params, [k for k, v in params.items() if v.isdigit()]


def _with(p, params, name, value):
    q = dict(params)
    q[name] = str(value)
    return urlunparse(p._replace(query=urlencode(q)))


def _check_forced_browsing(ctx) -> list[Finding]:
    from urllib.parse import urljoin
    findings = []
    root = urljoin(ctx.base_url, "/")
    for path, label in PROTECTED_PATHS:
        url = urljoin(root, path)
        # Oturumsuz (kullanıcının verdiği çerezleri atlayan) ayrı istek
        r = ctx.client.get(url, allow_redirects=False)
        if r is None or r.status_code != 200:
            continue
        low = (r.text or "")[:600].lower()
        if any(h in low for h in ("login", "giriş", "sign in", "unauthorized", "oturum aç")):
            continue  # giriş sayfasına düşmüş; korunuyor
        if len(r.text or "") < 80:
            continue
        findings.append(Finding(NAME, f"Korunması gereken sayfa kimlik doğrulamasız erişilebilir: /{path}",
            Severity.HIGH, url,
            f"{label} kimlik doğrulaması olmadan 200 döndürüyor ve giriş sayfasına yönlendirmiyor. "
            "Bu, bozuk erişim kontrolü (broken access control) olabilir.",
            "Bu uç noktayı sunucu tarafında kimlik doğrulama ve yetkilendirme ile koruyun.",
            f"HTTP 200, {len(r.text)} bayt, giriş istemiyor"))
    return findings


def _check_idor(ctx) -> list[Finding]:
    findings = []
    reported = set()
    for url in ctx.crawl.param_urls[:20]:
        p, params, numerics = _numeric_params(url)
        for name in numerics:
            key = (p.path, name)
            if key in reported:
                continue
            base_val = int(params[name])
            base_resp = ctx.client.get(_with(p, params, name, base_val))
            if not _looks_like_record(base_resp):
                continue
            # Komşu kimlikleri dene
            hits = []
            for delta in (-1, 1):
                nv = base_val + delta
                if nv < 0:
                    continue
                r = ctx.client.get(_with(p, params, name, nv))
                if _looks_like_record(r) and r.text != base_resp.text:
                    hits.append(nv)
            if hits:
                reported.add(key)
                findings.append(Finding(NAME, f"Sıralı kimlikler numaralandırılabilir (olası IDOR): '{name}'",
                    Severity.MEDIUM, url,
                    f"'{name}' parametresindeki numeric kimlik değiştirildiğinde ({base_val} ve "
                    f"{', '.join(map(str, hits))}) farklı geçerli kayıtlar erişilebiliyor; erişim kontrolü "
                    "olmadan bu, başka kullanıcıların verilerine erişim (IDOR) anlamına gelebilir. "
                    "Kesin doğrulama için iki farklı hesapla test gerekir.",
                    "Her nesne erişiminde sahiplik/yetki kontrolü yapın; tahmin edilemez tanımlayıcılar "
                    "(UUID) kullanmayı değerlendirin.",
                    f"{name}={base_val} ve {name}={hits[0]} ayrı geçerli içerik döndürdü"))
    return findings


def _check_auth_diff(ctx) -> list[Finding]:
    """Kullanıcı oturum çerezi verdiyse: oturumlu vs oturumsuz fark."""
    findings = []
    # Yalnızca kullanıcı açıkça kimlik bilgisi verdiyse çalış (sitenin kendi
    # set ettiği oturum çerezinden kaynaklı yanlış pozitifleri önlemek için).
    if not getattr(ctx, "authenticated", False):
        return findings
    import requests
    bare = requests.Session()
    bare.headers["User-Agent"] = ctx.client.session.headers.get("User-Agent", "Koruma")
    bare.verify = ctx.client.session.verify
    checked = 0
    for page in ctx.crawl.pages:
        if checked >= 10 or "html" not in page.content_type:
            continue
        try:
            auth_r = ctx.client.get(page.url)
            bare_r = bare.get(page.url, timeout=ctx.client.timeout, allow_redirects=True)
        except Exception:
            continue
        checked += 1
        if auth_r is None:
            continue
        # Oturumlu ve oturumsuz yanıt benzer uzunlukta ve 200 ise: koruma yok olabilir
        if (bare_r.status_code == 200 and auth_r.status_code == 200
                and len(bare_r.text) > 200
                and abs(len(bare_r.text) - len(auth_r.text)) < max(100, len(auth_r.text) * 0.1)):
            # Sayfa gerçekten korunmalı görünüyor mu? (çerez verdiyse muhtemelen giriş gerektiren alan)
            if any(w in auth_r.text.lower() for w in ("çıkış", "logout", "hesabım", "profil", "dashboard")):
                findings.append(Finding(NAME, "Oturum gerektiren içerik oturumsuz da erişilebilir",
                    Severity.HIGH, page.url,
                    "Bu sayfa kimlik doğrulamalı oturumla aynı içeriği oturum olmadan da döndürüyor; "
                    "erişim kontrolü eksik olabilir.",
                    "Hassas sayfalarda sunucu tarafında oturum/yetki kontrolü uygulayın.",
                    f"oturumlu {len(auth_r.text)} bayt ≈ oturumsuz {len(bare_r.text)} bayt"))
                break
    return findings


def run(ctx) -> list[Finding]:
    findings = []
    findings += _check_forced_browsing(ctx)
    findings += _check_idor(ctx)
    findings += _check_auth_diff(ctx)
    return findings
