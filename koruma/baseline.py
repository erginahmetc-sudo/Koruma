"""Catch-all (soft-404 / SPA) parmak izi.

Tek sayfa uygulamaları (SPA) ve bazı sunucular bilinmeyen HER adrese ana sayfayı
`200 OK` ile döndürür. Bu durumda "200 döndü" demek "dosya var" demek değildir;
tarayıcı bunu bilmezse `.env`, `/admin/` gibi yolları açık sanıp sahte alarm üretir.

Çözüm: kontroller çalışmadan önce, kesinlikle var olmayan rastgele adresler
istenir ve verilen cevapların parmak izi çıkarılır. Sonradan test edilen bir
cevap bu parmak izlerinden birine benziyorsa "yok" sayılır.
"""
from __future__ import annotations

import difflib
import hashlib
import re
import secrets

# Her istekte değişen kısımlar (nonce, hash, zaman damgası...) benzerlik
# karşılaştırmasını bozmasın diye silinir.
_NORMALIZERS = [
    (re.compile(r'nonce="[^"]*"', re.I), 'nonce=""'),
    (re.compile(r"\b[0-9a-f]{16,}\b", re.I), "H"),
    (re.compile(r"\d{6,}"), "N"),
    (re.compile(r"\s+"), " "),
]
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_HTML_HINT = re.compile(r"<\s*(?:!doctype\s+html|html|head|body|script|div|meta|title)\b", re.I)


def normalize(text: str) -> str:
    text = text[:20000]
    for rx, repl in _NORMALIZERS:
        text = rx.sub(repl, text)
    return text.strip()


def _title(text: str) -> str:
    m = _TITLE.search(text[:5000])
    return re.sub(r"\s+", " ", m.group(1)).strip().lower() if m else ""


def _family(ctype: str) -> str:
    c = (ctype or "").lower()
    if "html" in c:
        return "html"
    if "json" in c:
        return "json"
    if "xml" in c:
        return "xml"
    if "javascript" in c:
        return "js"
    if c.startswith("text/"):
        return "text"
    return "other"


def looks_html(text: str, ctype: str = "") -> bool:
    """Cevap bir HTML sayfası (kabuk/hata/giriş sayfası) gibi mi görünüyor?"""
    if "html" in (ctype or "").lower():
        return True
    return bool(_HTML_HINT.search(text[:1000]))


class _Sig:
    __slots__ = ("status", "family", "length", "digest", "title", "sample")

    def __init__(self, status: int, ctype: str, text: str):
        norm = normalize(text)
        self.status = status
        self.family = _family(ctype)
        self.length = len(text)
        self.digest = hashlib.sha1(norm.encode("utf-8", "replace")).hexdigest()
        self.title = _title(text)
        self.sample = norm[:3000]


class Baseline:
    def __init__(self, sigs: list[_Sig]):
        self.sigs = sigs

    @property
    def catchall(self) -> bool:
        """Var olmayan adresler 200 mü dönüyor? (SPA / soft-404)"""
        return any(s.status == 200 for s in self.sigs)

    def matches(self, status: int, ctype: str, text: str) -> bool:
        """Bu cevap, "olmayan adres" cevabına benziyor mu?"""
        if not self.sigs:
            return False
        norm = normalize(text)
        digest = hashlib.sha1(norm.encode("utf-8", "replace")).hexdigest()
        fam = _family(ctype)
        title = _title(text)
        for s in self.sigs:
            if s.status != status:
                continue
            if digest == s.digest:
                return True
            if fam != s.family:
                continue
            close = abs(len(text) - s.length) <= max(120, int(s.length * 0.05))
            if close and (title and title == s.title):
                return True
            if close or (title and title == s.title):
                ratio = difflib.SequenceMatcher(None, norm[:3000], s.sample).ratio()
                if ratio >= 0.93:
                    return True
        return False

    def matches_response(self, resp) -> bool:
        return self.matches(resp.status_code, resp.headers.get("Content-Type", ""), resp.text or "")


def _probe_paths() -> list[str]:
    r = secrets.token_hex(6)
    return [f"/{r}", f"/{r}.txt", f"/{r}.php", f"/{r}.json", f"/{r}/",
            f"/{r}/{r}", f"/.{r}", f"/static/{r}.js"]


def get(ctx) -> Baseline:
    """Siteye özgü parmak izini bir kez çıkarıp ctx üzerinde önbelleğe alır."""
    cached = getattr(ctx, "_baseline", None)
    if cached is not None:
        return cached
    sigs: list[_Sig] = []
    for path in _probe_paths():
        r = ctx.client.get(ctx.base_url.rstrip("/") + path, allow_redirects=False)
        if r is None:
            continue
        sigs.append(_Sig(r.status_code, r.headers.get("Content-Type", ""), r.text or ""))
    bl = Baseline(sigs)
    try:
        ctx._baseline = bl
    except Exception:
        pass
    return bl
