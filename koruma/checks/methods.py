from __future__ import annotations

from koruma.models import Finding, Severity

NAME = "methods"


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    url = ctx.base_url

    r = ctx.client.request("OPTIONS", url)
    if r is not None:
        allow = (r.headers.get("Allow", "") + "," + r.headers.get("Access-Control-Allow-Methods", "")).upper()
        risky = sorted({m for m in ("PUT", "DELETE", "PATCH", "PROPFIND", "MOVE", "COPY") if m in allow})
        if risky:
            findings.append(Finding(NAME, "Riskli HTTP metotları ilan ediliyor", Severity.LOW, url,
                                    f"Sunucu {', '.join(risky)} metotlarına izin verdiğini bildiriyor.",
                                    "Kullanılmayan metotları sunucu yapılandırmasında kapatın.",
                                    f"Allow: {allow.strip(',')}"))

    # TRACE yalnızca isteği geri yansıtır; zararsızdır.
    marker = "koruma-trace-test"
    r = ctx.client.request("TRACE", url, headers={"X-Koruma": marker})
    if r is not None and r.status_code == 200 and marker in r.text:
        findings.append(Finding(NAME, "HTTP TRACE metodu etkin", Severity.LOW, url,
                                "TRACE, Cross-Site Tracing (XST) saldırılarında kullanılabilir.",
                                "Apache: 'TraceEnable off'. Nginx varsayılan olarak kapalıdır."))
    return findings
