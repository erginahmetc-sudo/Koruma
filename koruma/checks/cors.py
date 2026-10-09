from __future__ import annotations

from urllib.parse import urlparse

from koruma.models import Finding, Severity

NAME = "cors"


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    host = urlparse(ctx.base_url).hostname
    targets = [ctx.base_url] + [p.url for p in ctx.crawl.pages if "json" in p.content_type][:5]
    probes = [
        ("https://koruma-test-evil.example", "Herhangi bir köken (origin) kabul ediliyor"),
        ("null", "'null' kökeni kabul ediliyor"),
        (f"https://{host}.koruma-test-evil.example", "Köken kontrolü önek eşleşmesiyle atlatılabiliyor"),
    ]
    reported = set()
    for url in targets:
        for origin, title in probes:
            r = ctx.client.get(url, headers={"Origin": origin})
            if r is None:
                continue
            acao = r.headers.get("Access-Control-Allow-Origin", "")
            acac = r.headers.get("Access-Control-Allow-Credentials", "").lower() == "true"
            if acao == origin and (title, url) not in reported:
                reported.add((title, url))
                sev = Severity.HIGH if acac else Severity.MEDIUM
                findings.append(Finding(NAME, f"CORS: {title}", sev, url,
                                        "Sunucu gelen Origin başlığını olduğu gibi geri yansıtıyor."
                                        + (" Kimlik bilgileriyle birlikte; kötü niyetli bir site oturum açmış kullanıcının verilerini okuyabilir." if acac else ""),
                                        "Access-Control-Allow-Origin için yalnızca güvendiğiniz kökenlerin beyaz listesini kullanın.",
                                        f"Origin: {origin} -> ACAO: {acao}, ACAC: {acac}"))
        r = ctx.client.get(url)
        if r is not None and r.headers.get("Access-Control-Allow-Origin") == "*" and ("CORS *", url) not in reported:
            reported.add(("CORS *", url))
            findings.append(Finding(NAME, "CORS: Access-Control-Allow-Origin: *", Severity.INFO, url,
                                    "Her site bu yanıtı okuyabilir. Herkese açık içerik için normaldir.",
                                    "Yanıt kullanıcıya özel veri içeriyorsa joker karakteri kaldırın."))
    return findings
