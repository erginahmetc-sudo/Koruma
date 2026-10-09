"""Derin JavaScript keşfi (recon) — en iyi bug bounty avcılarının yaptığı gibi.

Aynı kökenli JS dosyalarını indirip içlerinde:
  - gömülü sırlar/anahtarlar (API key, token, özel anahtar),
  - kaynak haritası (.js.map) ifşası — tüm kaynak kodu açığa çıkar,
  - gizli/riskli uç noktalar (admin, debug, internal API),
  - bulut/iç ağ adresleri
arar. Bu dosyalar genelde taranmaz ama en ciddi sızıntılar buradadır.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from koruma.checks.disclosure import PATTERNS
from koruma.models import Finding, Severity
from koruma.sitedata import collect

NAME = "jsrecon"

SOURCEMAP_COMMENT = re.compile(r"//[#@]\s*sourceMappingURL=([^\s'\"]+)")
# JS içinde geçen ilginç uç nokta yolları
ENDPOINT = re.compile(r"[\"'`](/(?:api|v\d|graphql|internal|admin|debug|private|actuator|_next/data)[/\w.\-]*)[\"'`]")
RISKY_WORDS = ("admin", "internal", "debug", "private", "secret", "token", "staging", "test")
PRIVATE_URL = re.compile(r"https?://(?:localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+|[a-z0-9.-]+\.(?:internal|local|corp))[:/\w.\-]*", re.I)


def run(ctx) -> list[Finding]:
    findings = []
    reported = set()

    def add(f, key):
        if key not in reported:
            reported.add(key)
            findings.append(f)

    data = collect(ctx)
    host = urlparse(ctx.base_url).hostname

    for url, content in data.scripts:
        # 1) Gömülü sırlar
        for label, sev, rx in PATTERNS:
            m = rx.search(content)
            if m:
                val = m.group(0)
                add(Finding(NAME, f"JS dosyasında gömülü sır: {label}", sev, url,
                    "İstemciye sunulan JavaScript dosyasında gizli bir anahtar/token bulunuyor; bu dosya "
                    "herkese açıktır ve anahtar herkes tarafından çıkarılabilir.",
                    "Anahtarı iptal edip döndürün; gizli bilgileri yalnızca sunucu tarafında tutun.",
                    f"{url.rsplit('/', 1)[-1]}: {val[:8]}…"), (label, val))

        # 2) Kaynak haritası ifşası
        for mm in SOURCEMAP_COMMENT.finditer(content):
            map_url = urljoin(url, mm.group(1))
            if urlparse(map_url).hostname != host or not map_url.startswith(("http://", "https://")):
                continue
            r = ctx.client.get(map_url) if ctx.client.in_scope(map_url) else None
            if r is not None and r.status_code == 200 and ('"sources"' in r.text[:2000] or '"mappings"' in r.text[:2000]):
                add(Finding(NAME, "Kaynak haritası (source map) herkese açık", Severity.MEDIUM, map_url,
                    "JavaScript kaynak haritası erişilebilir; bu, derlenmemiş/orijinal kaynak kodunuzun "
                    "(iç mantık, yorumlar, olası sırlar) yeniden elde edilebileceği anlamına gelir.",
                    "Üretimde kaynak haritalarını yayımlamayın veya erişimi engelleyin.",
                    map_url.rsplit("/", 1)[-1]), ("sourcemap", map_url))

        # 3) İç ağ / özel adresler
        pu = PRIVATE_URL.search(content)
        if pu:
            add(Finding(NAME, "JS içinde iç ağ/özel adres", Severity.LOW, url,
                "JavaScript'te iç ağ veya yerel bir adres ifşa oluyor; iç altyapı hakkında bilgi verir.",
                "İç adresleri üretim JS'inden çıkarın.", pu.group(0)[:80]), ("privurl", pu.group(0)))

        # 4) Riskli/gizli uç noktalar
        eps = set()
        for mm in ENDPOINT.finditer(content):
            path = mm.group(1)
            if any(w in path.lower() for w in RISKY_WORDS):
                eps.add(path)
        for path in list(eps)[:6]:
            add(Finding(NAME, f"JS'te gizli/riskli uç nokta referansı: {path}", Severity.INFO, url,
                "Arayüzde görünmeyen bir API/yönetim uç noktası JavaScript'te referans veriliyor. Bu tür "
                "uç noktalar IDOR, yetki yükseltme ve iş mantığı açıklarına yol açabilir.",
                "Bu uç noktanın kimlik doğrulama ve yetkilendirmeyle korunduğundan emin olun.",
                path), ("endpoint", path))

    return findings
