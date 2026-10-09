from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup

from koruma.http import Client
from koruma.models import Form

SKIP_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".css", ".woff",
    ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".pdf", ".zip", ".gz", ".tar",
)
# Bu kelimeleri içeren bağlantılara gidilmez; oturum kapatma veya veri silme
# gibi yan etkileri tetiklememek için.
DANGEROUS_WORDS = ("logout", "signout", "cikis", "çıkış", "delete", "remove", "sil", "destroy")


@dataclass
class Page:
    url: str
    status: int
    headers: dict[str, str]
    body: str
    content_type: str


@dataclass
class CrawlResult:
    pages: list[Page] = field(default_factory=list)
    forms: list[Form] = field(default_factory=list)
    param_urls: list[str] = field(default_factory=list)


def _normalize(url: str) -> str:
    return urldefrag(url)[0]


def _record_params(url: str, result: CrawlResult, seen: set) -> None:
    parsed = urlparse(url)
    if not parsed.query:
        return
    shape = (parsed.path, tuple(sorted(parse_qs(parsed.query))))
    if shape not in seen:
        seen.add(shape)
        result.param_urls.append(url)


def parse_forms(page_url: str, html: str) -> list[Form]:
    soup = BeautifulSoup(html, "html.parser")
    forms = []
    for f in soup.find_all("form"):
        action = urljoin(page_url, f.get("action") or page_url)
        method = (f.get("method") or "get").lower()
        inputs: dict[str, str] = {}
        for el in f.find_all(["input", "textarea", "select"]):
            name = el.get("name")
            if not name:
                continue
            itype = (el.get("type") or "text").lower()
            if itype in ("submit", "button", "image", "file", "reset"):
                continue
            inputs[name] = el.get("value") or ""
        forms.append(Form(action=action, method=method, inputs=inputs, page_url=page_url))
    return forms


def crawl(client: Client, start_url: str, max_pages: int = 50, log=print) -> CrawlResult:
    result = CrawlResult()
    seen: set[str] = set()
    seen_param_shapes: set[tuple] = set()
    seen_forms: set[tuple] = set()
    queue = deque([_normalize(start_url)])

    while queue and len(result.pages) < max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        resp = client.get(url)
        if resp is None:
            continue
        final = _normalize(resp.url)
        if not client.in_scope(final):
            continue
        ctype = resp.headers.get("Content-Type", "")
        page = Page(final, resp.status_code, dict(resp.headers), resp.text if "text" in ctype or "json" in ctype else "", ctype)
        result.pages.append(page)
        log(f"  [{resp.status_code}] {final}")

        _record_params(final, result, seen_param_shapes)

        if "html" not in ctype:
            continue

        for form in parse_forms(final, page.body):
            fkey = (form.action, form.method, tuple(sorted(form.inputs)))
            if fkey not in seen_forms and client.in_scope(form.action):
                seen_forms.add(fkey)
                result.forms.append(form)

        soup = BeautifulSoup(page.body, "html.parser")
        for tag in soup.find_all(["a", "link", "iframe", "frame"]):
            href = tag.get("href") or tag.get("src")
            if not href or href.startswith(("mailto:", "javascript:", "tel:", "data:")):
                continue
            link = _normalize(urljoin(final, href))
            low = link.lower()
            if urlparse(link).scheme not in ("http", "https") or not client.in_scope(link):
                continue
            if urlparse(low).path.endswith(SKIP_EXTENSIONS):
                continue
            # Parametreli bağlantıları, ziyaret etmeden önce kaydet: yönlendirme
            # yapan URL'ler yönlendirme sonrası sorgu dizesini kaybeder.
            _record_params(link, result, seen_param_shapes)
            if link not in seen and not any(w in low for w in DANGEROUS_WORDS):
                queue.append(link)
    return result
