"""Site içeriğini bir kez toplayıp birden fazla kontrolün paylaşmasını sağlar:
HTML gövdeleri + aynı kökenli JavaScript dosyalarının içeriği.

Tarayıcı normalde <script src> dosyalarını indirmez; backend/sır keşfi için
burada (sınırlı sayıda) indirilir ve ctx üzerinde önbelleğe alınır.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


@dataclass
class SiteData:
    html_text: str = ""                 # tüm HTML gövdeleri birleşik
    scripts: list = field(default_factory=list)  # (url, content) aynı kökenli JS
    script_srcs: list = field(default_factory=list)  # tüm <script src> (çapraz dahil)
    combined: str = ""                  # HTML + JS birleşik (regex için)


def collect(ctx, max_scripts: int = 15, max_bytes: int = 400_000) -> SiteData:
    cached = getattr(ctx, "_sitedata", None)
    if cached is not None:
        return cached

    host = urlparse(ctx.base_url).hostname
    data = SiteData()
    html_parts = []
    srcs = []
    seen = set()

    for page in ctx.crawl.pages:
        if page.body:
            html_parts.append(page.body)
        if "html" not in page.content_type or not page.body:
            continue
        soup = BeautifulSoup(page.body, "html.parser")
        for tag in soup.find_all("script"):
            src = tag.get("src")
            if src:
                full = urljoin(page.url, src)
                if full not in seen:
                    seen.add(full)
                    srcs.append(full)

    data.html_text = "\n".join(html_parts)[:max_bytes * 2]
    data.script_srcs = srcs

    # Aynı kökenli JS dosyalarını indir (sınırlı)
    fetched = 0
    js_text = []
    for full in srcs:
        if fetched >= max_scripts:
            break
        if urlparse(full).hostname != host:
            continue
        if not ctx.client.in_scope(full):
            continue
        resp = ctx.client.get(full)
        if resp is None:
            continue
        ct = resp.headers.get("Content-Type", "")
        if "javascript" not in ct and "text" not in ct and not full.endswith(".js"):
            continue
        content = resp.text[:max_bytes]
        data.scripts.append((full, content))
        js_text.append(content)
        fetched += 1

    data.combined = (data.html_text + "\n" + "\n".join(js_text))[:max_bytes * 3]
    try:
        ctx._sitedata = data
    except Exception:
        pass
    return data
