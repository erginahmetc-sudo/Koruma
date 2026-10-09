from __future__ import annotations

import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

from koruma.models import Finding, Severity

NAME = "tls"


def _cert_info(host: str, port: int, timeout: float):
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            return ssock.getpeercert(), ssock.version()


def _accepts_old_tls(host: str, port: int, version: ssl.TLSVersion, timeout: float) -> bool:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.minimum_version = version
        ctx.maximum_version = version
        ctx.set_ciphers("ALL:@SECLEVEL=0")
    except (ValueError, ssl.SSLError):
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host):
                return True
    except (OSError, ssl.SSLError):
        return False


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    parsed = urlparse(ctx.base_url)
    host = parsed.hostname

    if parsed.scheme == "http":
        findings.append(Finding(NAME, "Site HTTPS kullanmıyor", Severity.HIGH, ctx.base_url,
                                "Trafik şifrelenmeden gönderiliyor; parolalar ve oturum çerezleri ağda okunabilir.",
                                "Let's Encrypt gibi ücretsiz bir sertifika ile HTTPS'i etkinleştirin."))
        for form in ctx.crawl.forms:
            if any("pass" in n.lower() or "sifre" in n.lower() for n in form.inputs):
                findings.append(Finding(NAME, "Parola formu şifresiz bağlantı üzerinden gönderiliyor", Severity.HIGH,
                                        form.page_url, "Parolalar düz metin olarak iletilir.",
                                        "Tüm siteyi HTTPS'e taşıyın.", f"form action={form.action}"))
        return findings

    port = parsed.port or 443
    timeout = ctx.client.timeout

    # HTTP -> HTTPS yönlendirmesi
    http_url = f"http://{host}/"
    r = ctx.client.get(http_url, allow_redirects=False)
    if r is not None and not (300 <= r.status_code < 400 and r.headers.get("Location", "").startswith("https://")):
        findings.append(Finding(NAME, "HTTP isteği HTTPS'e yönlendirilmiyor", Severity.MEDIUM, http_url,
                                "Kullanıcılar şifresiz sürümü kullanmaya devam edebilir.",
                                "Port 80'deki tüm istekleri 301 ile HTTPS'e yönlendirin.",
                                f"HTTP {r.status_code}"))

    # HSTS
    home = next((p for p in ctx.crawl.pages if p.url.startswith("https://")), None)
    if home:
        hsts = {k.lower(): v for k, v in home.headers.items()}.get("strict-transport-security")
        if not hsts:
            findings.append(Finding(NAME, "HSTS başlığı eksik", Severity.MEDIUM, home.url,
                                    "Tarayıcılar ilk ziyarette şifresiz bağlantıya düşürülebilir (SSL stripping).",
                                    "Strict-Transport-Security: max-age=31536000; includeSubDomains ekleyin."))
        else:
            try:
                max_age = int(hsts.lower().split("max-age=")[1].split(";")[0].strip())
                if max_age < 15552000:
                    findings.append(Finding(NAME, "HSTS max-age değeri düşük", Severity.LOW, home.url,
                                            "6 aydan kısa max-age koruma süresini azaltır.",
                                            "max-age değerini en az 31536000 yapın.", hsts))
            except (IndexError, ValueError):
                pass

    # Sertifika
    try:
        cert, version = _cert_info(host, port, timeout)
        not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        days = (not_after - datetime.now(timezone.utc)).days
        if days < 0:
            sev, title = Severity.CRITICAL, "TLS sertifikasının süresi dolmuş"
        elif days < 14:
            sev, title = Severity.HIGH, f"TLS sertifikası {days} gün içinde sona eriyor"
        elif days < 30:
            sev, title = Severity.MEDIUM, f"TLS sertifikası {days} gün içinde sona eriyor"
        else:
            sev = None
        if sev is not None:
            findings.append(Finding(NAME, title, sev, ctx.base_url, "Süresi dolan sertifika ziyaretçilere uyarı gösterir.",
                                    "Sertifikayı yenileyin ve otomatik yenilemeyi kurun.", f"notAfter={cert['notAfter']}"))
    except ssl.SSLCertVerificationError as e:
        findings.append(Finding(NAME, "TLS sertifikası doğrulanamadı", Severity.HIGH, ctx.base_url,
                                "Geçersiz, kendinden imzalı veya alan adıyla eşleşmeyen sertifika.",
                                "Güvenilir bir CA'dan, alan adıyla eşleşen sertifika alın.", str(e)))
    except (OSError, ssl.SSLError):
        pass

    for ver, label in ((ssl.TLSVersion.TLSv1, "TLS 1.0"), (ssl.TLSVersion.TLSv1_1, "TLS 1.1")):
        if _accepts_old_tls(host, port, ver, timeout):
            findings.append(Finding(NAME, f"Eski protokol destekleniyor: {label}", Severity.MEDIUM, ctx.base_url,
                                    f"{label} artık güvenli kabul edilmiyor.",
                                    "Sunucuda yalnızca TLS 1.2 ve TLS 1.3'ü etkin bırakın."))
    return findings
