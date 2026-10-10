"""Açıkta kalan uç noktalar ve hizmetler.

GraphQL introspection, yönetim/API panelleri, çapraz alan politika dosyaları
ve WordPress kullanıcı sayımı (user enumeration) gibi, saldırganların keşif
aşamasında aradığı uç noktaları kontrol eder. Hepsi salt-okunur isteklerdir.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urljoin

from koruma import baseline
from koruma.models import Finding, Severity

NAME = "endpoints"

GRAPHQL_PATHS = ["graphql", "api/graphql", "v1/graphql", "query", "graphiql"]
INTROSPECTION = {"query": "{__schema{queryType{name}}}"}

ADMIN_PATHS = [
    ("admin/", Severity.INFO, "Yönetim paneli"),
    ("administrator/", Severity.INFO, "Joomla yönetim paneli"),
    ("wp-admin/", Severity.INFO, "WordPress yönetim paneli"),
    ("manager/html", Severity.MEDIUM, "Tomcat Manager"),
    ("jenkins/", Severity.MEDIUM, "Jenkins"),
    ("api/", Severity.INFO, "API kökü"),
    ("api/v1/", Severity.INFO, "API v1"),
    ("api-docs", Severity.INFO, "API dokümantasyonu"),
    ("swagger-ui.html", Severity.INFO, "Swagger arayüzü"),
    ("actuator", Severity.MEDIUM, "Spring Boot Actuator"),
    ("metrics", Severity.LOW, "Metrik uç noktası"),
    ("debug/pprof/", Severity.HIGH, "Go pprof hata ayıklama"),
    ("console", Severity.LOW, "Yönetim konsolu"),
    ("phpmyadmin/", Severity.MEDIUM, "phpMyAdmin"),
    (".well-known/security.txt", None, None),
]

CROSS_DOMAIN = [
    ("crossdomain.xml", r"allow-access-from\s+domain\s*=\s*[\"']\*[\"']",
     "Flash çapraz alan politikası her kaynağa izin veriyor"),
    ("clientaccesspolicy.xml", r"domain\s+uri\s*=\s*[\"']\*[\"']",
     "Silverlight çapraz alan politikası her kaynağa izin veriyor"),
]


def _ok(resp, soft=None):
    return resp is not None and resp.status_code == 200


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    root = urljoin(ctx.base_url, "/")
    bl = baseline.get(ctx)   # SPA / catch-all parmak izi (sahte alarm önleme)

    # --- GraphQL introspection ---
    for path in GRAPHQL_PATHS:
        url = urljoin(root, path)
        r = ctx.client.request("POST", url, json=INTROSPECTION)
        if r is None or r.status_code not in (200, 400):
            continue
        try:
            data = r.json()
        except (ValueError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("data", {}).get("__schema"):
            findings.append(Finding(NAME, "GraphQL introspection açık", Severity.MEDIUM, url,
                "GraphQL şeması introspection ile tümüyle okunabiliyor; tüm tipler, sorgular ve "
                "mutasyonlar saldırgana ifşa oluyor.",
                "Üretimde introspection'ı kapatın ve GraphiQL/Playground arayüzünü yayınlamayın.",
                "POST __schema sorgusu 200 döndü"))
            break

    # --- Yönetim / API uç noktaları ---
    for path, sev, label in ADMIN_PATHS:
        if sev is None:
            continue
        url = urljoin(root, path)
        r = ctx.client.get(url, allow_redirects=False)
        if r is None or bl.matches_response(r):   # sunucunun "olmayan adres" cevabına benziyor
            continue
        if r.status_code in (200, 401, 403) or (r.status_code in (301, 302) and path.rstrip("/") in r.headers.get("Location", "")):
            state = {200: "erişilebilir", 401: "kimlik doğrulama istiyor", 403: "yasak",
                     301: "yönlendiriyor", 302: "yönlendiriyor"}.get(r.status_code, str(r.status_code))
            findings.append(Finding(NAME, f"Uç nokta mevcut: /{path} ({label})", sev, url,
                f"{label} uç noktası bulundu (HTTP {r.status_code}, {state}). Açık yönetim/araç "
                "arayüzleri saldırı yüzeyini artırır.",
                "Gerekmiyorsa kaldırın; gerekiyorsa IP kısıtlaması/kimlik doğrulamayla koruyun.",
                f"HTTP {r.status_code}"))

    # --- Çapraz alan politika dosyaları ---
    for fname, marker, desc in CROSS_DOMAIN:
        url = urljoin(root, fname)
        r = ctx.client.get(url)
        if _ok(r) and not bl.matches_response(r) and r.text.lstrip().startswith("<"):
            if re.search(marker, r.text, re.I):
                findings.append(Finding(NAME, f"Gevşek çapraz alan politikası: /{fname}", Severity.MEDIUM, url,
                    desc + ". Bu, başka sitelerin tarayıcı üzerinden verilerinize erişmesine izin verebilir.",
                    "Politikayı yalnızca güvendiğiniz alan adlarıyla sınırlayın veya dosyayı kaldırın.",
                    r.text[:120].replace("\n", " ")))

    # --- WordPress kullanıcı sayımı ---
    wp_api = urljoin(root, "wp-json/wp/v2/users")
    r = ctx.client.get(wp_api)
    if _ok(r):
        try:
            users = r.json()
            if isinstance(users, list) and users and "slug" in users[0]:
                names = ", ".join(u.get("slug", "?") for u in users[:5])
                findings.append(Finding(NAME, "WordPress kullanıcı sayımı (REST API)", Severity.MEDIUM, wp_api,
                    "wp-json/wp/v2/users uç noktası kullanıcı adlarını (slug) ifşa ediyor; bu adlar "
                    "kaba kuvvet (brute-force) saldırıları için kullanılabilir.",
                    "REST API users uç noktasına yetkisiz erişimi engelleyin (güvenlik eklentisi/sunucu kuralı).",
                    f"kullanıcılar: {names}"))
        except (ValueError, json.JSONDecodeError):
            pass

    # author=1 yönlendirmesi ile sayım
    r = ctx.client.get(urljoin(root, "?author=1"), allow_redirects=False)
    if r is not None and r.status_code in (301, 302) and "/author/" in r.headers.get("Location", ""):
        author = r.headers["Location"].rstrip("/").split("/author/")[-1]
        findings.append(Finding(NAME, "WordPress kullanıcı sayımı (?author=1)", Severity.LOW,
            urljoin(root, "?author=1"),
            "?author=N isteği yazar arşivine yönlenerek geçerli kullanıcı adını ifşa ediyor.",
            "Yazar arşivi yönlendirmesini kapatın veya kullanıcı adı ile görünen adı farklılaştırın.",
            f"-> /author/{author}/"))

    # XML-RPC
    r = ctx.client.get(urljoin(root, "xmlrpc.php"))
    if (r is not None and r.status_code in (200, 405) and not bl.matches_response(r)
            and "XML-RPC server accepts POST requests only" in r.text):
        findings.append(Finding(NAME, "WordPress XML-RPC etkin", Severity.LOW, urljoin(root, "xmlrpc.php"),
            "xmlrpc.php etkin; system.multicall ile tek istekte yüzlerce parola denemesi yapılabilir "
            "(kaba kuvvet güçlendirme) ve pingback DDoS'a yol açabilir.",
            "Gerekmiyorsa xmlrpc.php'yi sunucu düzeyinde engelleyin."))

    return findings
