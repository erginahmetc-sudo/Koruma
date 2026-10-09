from __future__ import annotations

import time
from dataclasses import dataclass, field

from koruma.checks import ALL_CHECKS, Context
from koruma.crawler import crawl
from koruma.http import Client
from koruma.models import Finding


@dataclass
class ScanResult:
    base_url: str
    findings: list[Finding] = field(default_factory=list)
    pages_crawled: int = 0
    forms_found: int = 0
    requests_made: int = 0
    duration: float = 0.0
    errors: list[str] = field(default_factory=list)


def scan(base_url: str, checks: list[str] | None = None, delay: float = 0.2,
         timeout: float = 10.0, max_pages: int = 50, verify_tls: bool = True,
         test_post_forms: bool = False, headers=None, cookies=None, log=print) -> ScanResult:
    start = time.monotonic()
    client = Client(base_url, delay=delay, timeout=timeout, verify_tls=verify_tls,
                    headers=headers, cookies=cookies)
    result = ScanResult(base_url=base_url)

    log("» Site taranıyor (crawl)...")
    crawl_res = crawl(client, base_url, max_pages=max_pages, log=log)
    result.pages_crawled = len(crawl_res.pages)
    result.forms_found = len(crawl_res.forms)
    log(f"  {result.pages_crawled} sayfa, {result.forms_found} form, "
        f"{len(crawl_res.param_urls)} parametreli URL bulundu.\n")

    if not crawl_res.pages:
        result.errors.append("Hiçbir sayfaya ulaşılamadı; URL ve ağ erişimini kontrol edin.")

    ctx = Context(client=client, base_url=base_url, crawl=crawl_res,
                  test_post_forms=test_post_forms, log=log)

    selected = checks or list(ALL_CHECKS)
    for name in selected:
        module = ALL_CHECKS.get(name)
        if module is None:
            result.errors.append(f"Bilinmeyen kontrol: {name}")
            continue
        log(f"» Kontrol: {name}")
        try:
            found = module.run(ctx)
            result.findings.extend(found)
            log(f"  {len(found)} bulgu.")
        except Exception as e:  # tek bir kontrolün hatası taramayı durdurmasın
            result.errors.append(f"{name} kontrolü hata verdi: {e}")
            log(f"  ! hata: {e}")

    result.findings.sort(key=lambda f: (-int(f.severity), f.check, f.title))
    result.requests_made = client.request_count
    result.duration = time.monotonic() - start
    return result
