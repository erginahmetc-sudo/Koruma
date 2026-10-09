from __future__ import annotations

import re

from koruma.models import Finding, Severity

NAME = "disclosure"

PATTERNS = [
    ("AWS erişim anahtarı", Severity.CRITICAL, re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API anahtarı", Severity.MEDIUM, re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Stripe gizli anahtarı", Severity.CRITICAL, re.compile(r"\bsk_live_[0-9a-zA-Z]{24,}\b")),
    ("GitHub token", Severity.CRITICAL, re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("Slack token", Severity.HIGH, re.compile(r"\bxox[baprs]-[0-9A-Za-z\-]{10,}\b")),
    ("Özel anahtar (private key)", Severity.CRITICAL, re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

ERROR_PATTERNS = [
    ("PHP hata mesajı", re.compile(r"<b>(?:Fatal error|Warning|Parse error|Notice)</b>:.*? in <b>[^<]+</b> on line", re.S)),
    ("Python traceback", re.compile(r"Traceback \(most recent call last\)")),
    ("Java stack trace", re.compile(r"\bat [a-zA-Z0-9_.$]+\([A-Za-z0-9_]+\.java:\d+\)")),
    (".NET hata sayfası", re.compile(r"Server Error in '/' Application|<title>Runtime Error</title>")),
    ("Django debug sayfası", re.compile(r"You're seeing this error because you have <code>DEBUG = True</code>")),
    ("Laravel debug sayfası", re.compile(r"Whoops! There was an error|Illuminate\\\\")),
    ("Rails debug sayfası", re.compile(r"Action Controller: Exception caught")),
    ("ASP.NET/Express stack", re.compile(r"at Object\.<anonymous> \(/[^)]+\.js:\d+:\d+\)")),
]

PRIVATE_IP = re.compile(r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b")
HTML_COMMENT = re.compile(r"<!--(.*?)-->", re.S)
COMMENT_KEYWORDS = ("password", "parola", "şifre", "sifre", "todo", "fixme", "api_key", "apikey", "secret", "admin")


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    reported: set[tuple] = set()

    def add(f: Finding, dedupe_key):
        if dedupe_key not in reported:
            reported.add(dedupe_key)
            findings.append(f)

    for page in ctx.crawl.pages:
        body = page.body
        if not body:
            continue
        for label, sev, rx in PATTERNS:
            m = rx.search(body)
            if m:
                val = m.group(0)
                add(Finding(NAME, f"Sayfada gizli bilgi: {label}", sev, page.url,
                            "Gizli anahtarlar istemciye gönderilen içerikte bulunuyor.",
                            "Anahtarı hemen iptal edip yenileyin ve sunucu tarafında saklayın.",
                            val[:8] + "…" + val[-4:]), (label, val))
        for label, rx in ERROR_PATTERNS:
            if rx.search(body):
                add(Finding(NAME, f"Hata ayrıntısı ifşa ediliyor: {label}", Severity.MEDIUM, page.url,
                            "Hata mesajları dosya yolları, kod yapısı ve sürüm bilgisi sızdırır.",
                            "Üretim ortamında debug modunu kapatın ve genel hata sayfası gösterin."), (label, page.url))
        if "html" in page.content_type:
            for c in HTML_COMMENT.findall(body):
                low = c.lower()
                if any(k in low for k in COMMENT_KEYWORDS):
                    add(Finding(NAME, "HTML yorumunda hassas olabilecek içerik", Severity.LOW, page.url,
                                "HTML yorumları ziyaretçiler tarafından görülebilir.",
                                "Üretime çıkmadan yorumları temizleyin.", c.strip()[:150]), ("comment", c.strip()[:80]))
            ip = PRIVATE_IP.search(body)
            if ip:
                add(Finding(NAME, "İç ağ IP adresi ifşa ediliyor", Severity.LOW, page.url,
                            "Özel IP adresleri iç ağ yapısı hakkında bilgi verir.",
                            "İç IP adreslerini yanıtlardan çıkarın.", ip.group(0)), ("ip", ip.group(0)))
            if page.url.startswith("https://"):
                mixed = re.search(r"""<(?:script|iframe|link)[^>]+(?:src|href)=["']http://[^"']+""", body, re.I)
                if mixed:
                    add(Finding(NAME, "Karışık içerik (HTTPS sayfada HTTP kaynak)", Severity.MEDIUM, page.url,
                                "Şifresiz yüklenen scriptler ağdaki bir saldırgan tarafından değiştirilebilir.",
                                "Tüm kaynakları https:// ile yükleyin.", mixed.group(0)[:150]), ("mixed", page.url))
    return findings
