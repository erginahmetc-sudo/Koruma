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
    authenticated: bool = False
    log: object = field(default=print)


from koruma.checks import (  # noqa: E402
    access,
    advanced,
    baas,
    components,
    cookies,
    cors,
    disclosure,
    dns_email,
    endpoints,
    files,
    fingerprint,
    headers,
    injection,
    jsrecon,
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
    "endpoints": endpoints,
    "advanced": advanced,
    "dns_email": dns_email,
    "access": access,
    "baas": baas,
    "jsrecon": jsrecon,
}
