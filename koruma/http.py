from __future__ import annotations

import threading
import time
from urllib.parse import urlparse

import requests

from koruma import __version__


class Client:
    """Hız sınırlı, kapsam kontrollü HTTP istemcisi.

    Yalnızca hedef sitenin host'una istek atar; böylece tarayıcı
    yanlışlıkla üçüncü taraf sitelere test isteği göndermez.
    """

    def __init__(self, base_url: str, delay: float = 0.2, timeout: float = 10.0,
                 verify_tls: bool = True, headers: dict[str, str] | None = None,
                 cookies: dict[str, str] | None = None):
        self.base_url = base_url
        self.host = urlparse(base_url).hostname
        self.delay = delay
        self.timeout = timeout
        self.request_count = 0
        self._lock = threading.Lock()
        self._last = 0.0
        self.session = requests.Session()
        self.session.verify = verify_tls
        self.session.headers["User-Agent"] = f"Koruma/{__version__} (guvenlik-tarayicisi)"
        if headers:
            self.session.headers.update(headers)
        if cookies:
            self.session.cookies.update(cookies)

    def in_scope(self, url: str) -> bool:
        return urlparse(url).hostname == self.host

    def _throttle(self) -> None:
        with self._lock:
            wait = self.delay - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            self.request_count += 1

    def request(self, method: str, url: str, **kwargs) -> requests.Response | None:
        if not self.in_scope(url):
            raise ValueError(f"Kapsam dışı URL engellendi: {url}")
        self._throttle()
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("allow_redirects", True)
        try:
            return self.session.request(method, url, **kwargs)
        except requests.RequestException:
            return None

    def get(self, url: str, **kwargs) -> requests.Response | None:
        return self.request("GET", url, **kwargs)
