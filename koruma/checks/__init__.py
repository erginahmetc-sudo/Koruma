from __future__ import annotations

from dataclasses import dataclass, field

from koruma.crawler import CrawlResult
from koruma.http import Client


@dataclass
class Context:
    client: Client
    base_url: str
    crawl: CrawlResult
    test_post_forms: bool = False
    online: bool = False
    log: object = field(default=print)


from koruma.checks import (  # noqa: E402
    components,
    cookies,
    cors,
    disclosure,
    files,
    fingerprint,
    headers,
    injection,
    methods,
    redirect,
    tls,
)

ALL_CHECKS = {
    "headers": headers,
    "tls": tls,
    "cookies": cookies,
    "files": files,
    "cors": cors,
    "methods": methods,
    "disclosure": disclosure,
    "injection": injection,
    "redirect": redirect,
    "fingerprint": fingerprint,
    "components": components,
}
