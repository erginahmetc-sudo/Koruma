"""OWASP A06:2021 — Savunmasız ve Güncel Olmayan Bileşenler.

Sayfalardaki JavaScript kütüphanelerini ve sürümlerini tespit eder, bilinen
güvenlik açıklarıyla (CVE) eşleştirir. Ayrıca çapraz kökenli (cross-origin)
scriptlerde Subresource Integrity (SRI) eksikliğini bildirir (A08: bütünlük).

İsteğe bağlı olarak (--online) tespit edilen sürümleri OSV.dev veritabanıyla
doğrular/zenginleştirir.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from koruma import semver
from koruma.models import Finding, Severity

NAME = "components"
_PLACEHOLDER = "(§§version§§)"
_VERSION_RX = r"([0-9]+(?:\.[0-9]+){1,3}(?:-[0-9A-Za-z][0-9A-Za-z.]*)?)"
_SEV = {"LOW": Severity.LOW, "MEDIUM": Severity.MEDIUM, "HIGH": Severity.HIGH, "CRITICAL": Severity.CRITICAL}


@lru_cache(maxsize=1)
def _load_db() -> dict:
    path = Path(__file__).resolve().parent.parent / "data" / "js_vulns.json"
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    libs = data["libraries"]
    for lib in libs.values():
        lib["_compiled"] = [
            re.compile(pat.replace(_PLACEHOLDER, _VERSION_RX), re.I) for pat in lib["extractors"]
        ]
    return libs


def _detect_version(text: str, lib: dict) -> str | None:
    for rx in lib["_compiled"]:
        m = rx.search(text)
        if m:
            return m.group(1)
    return None


def _match_vulns(version: str, lib: dict) -> list[dict]:
    return [
        v for v in lib["vulns"]
        if semver.in_range(version, v.get("atOrAbove"), v.get("below"), v.get("above"))
    ]


def _collect_scripts(ctx):
    """(url, is_cross_origin, has_integrity) ve sayfa içi inline script metinleri."""
    host = urlparse(ctx.base_url).hostname
    scripts, inline = [], []
    seen = set()
    for page in ctx.crawl.pages:
        if "html" not in page.content_type or not page.body:
            continue
        soup = BeautifulSoup(page.body, "html.parser")
        for tag in soup.find_all("script"):
            src = tag.get("src")
            if src:
                if src in seen:
                    continue
                seen.add(src)
                cross = urlparse(src).hostname not in (None, host)
                scripts.append((src, cross, bool(tag.get("integrity")), page.url))
            elif tag.string and len(tag.string) > 40:
                inline.append((tag.string[:4000], page.url))
    return scripts, inline


def _osv_lookup(name: str, version: str, timeout: float):
    """OSV.dev'den npm ekosistemi için bilinen açıkları sorgular (isteğe bağlı)."""
    try:
        import requests
        r = requests.post("https://api.osv.dev/v1/query",
                          json={"version": version, "package": {"name": name, "ecosystem": "npm"}},
                          timeout=timeout)
        if r.status_code != 200:
            return []
        return [v.get("id") for v in r.json().get("vulns", []) if v.get("id")]
    except Exception:
        return []


def run(ctx) -> list[Finding]:
    findings: list[Finding] = []
    libs = _load_db()
    scripts, inline = _collect_scripts(ctx)
    online = getattr(ctx, "online", False)
    reported_sri = set()

    def report_lib(libname, version, where, source):
        lib = libs[libname]
        vulns = _match_vulns(version, lib)
        if not vulns:
            return
        max_sev = max(_SEV[v["severity"]] for v in vulns)
        all_ids = sorted({i for v in vulns for i in v["ids"]})
        summary = " ".join(dict.fromkeys(v["summary"] for v in vulns))
        findings.append(Finding(
            NAME, f"Savunmasız kütüphane: {libname} {version}", max_sev, where,
            f"{libname} {version} sürümünde bilinen güvenlik açıkları var ({len(vulns)} kayıt). " + summary,
            f"{libname} kütüphanesini güncel ve güvenli bir sürüme yükseltin.",
            f"{source} | {', '.join(all_ids)}"))

    # Harici/sürümlü script URL'leri
    for src, cross, has_integrity, page_url in scripts:
        abs_src = src if src.startswith(("http://", "https://")) else src
        for libname, lib in libs.items():
            if libname == "_meta":
                continue
            version = _detect_version(abs_src, lib)
            if version:
                report_lib(libname, version, page_url, abs_src)
                if online:
                    ids = _osv_lookup(libname, version, ctx.client.timeout)
                    if ids and not _match_vulns(version, lib):
                        findings.append(Finding(
                            NAME, f"OSV: {libname} {version} için bilinen açık", Severity.MEDIUM, page_url,
                            "OSV.dev veritabanı bu sürüm için güvenlik açığı bildiriyor.",
                            "Kütüphaneyi güncelleyin.", ", ".join(ids[:8])))
                break
        # SRI (çapraz kökenli scriptlerde bütünlük doğrulaması)
        if cross and not has_integrity and abs_src not in reported_sri:
            reported_sri.add(abs_src)
            findings.append(Finding(
                NAME, "Çapraz kökenli script'te SRI (bütünlük) yok", Severity.LOW, page_url,
                "Harici bir CDN'den integrity özniteliği olmadan script yükleniyor. CDN ele "
                "geçirilirse değiştirilmiş kod sessizce çalışır (tedarik zinciri riski).",
                "Script etiketine integrity ve crossorigin öznitelikleri ekleyin (SRI).",
                abs_src))

    # Inline script içeriğinden sürüm tespiti (ör. kendi sunucunuzdaki paketlenmiş kod)
    for text, page_url in inline:
        for libname, lib in libs.items():
            if libname == "_meta":
                continue
            version = _detect_version(text, lib)
            if version:
                report_lib(libname, version, page_url, "inline script")
                break

    # Aynı kökenli, sürümü ad/URL'den belli olmayan scriptleri indirip içeriğine bak
    host = urlparse(ctx.base_url).hostname
    checked = 0
    for src, cross, _hi, page_url in scripts:
        if cross or checked >= 8:
            continue
        full = src if src.startswith("http") else None
        if not full or not ctx.client.in_scope(full):
            continue
        if any(_detect_version(full, lib) for n, lib in libs.items() if n != "_meta"):
            continue  # zaten URL'den tespit edildi
        resp = ctx.client.get(full)
        checked += 1
        if resp is None or "javascript" not in resp.headers.get("Content-Type", "") and "text" not in resp.headers.get("Content-Type", ""):
            continue
        head = resp.text[:6000]
        for libname, lib in libs.items():
            if libname == "_meta":
                continue
            version = _detect_version(head, lib)
            if version:
                report_lib(libname, version, page_url, full)
                break

    # Yinelenenleri ele
    uniq, seen = [], set()
    for f in findings:
        if f.key() not in seen:
            seen.add(f.key())
            uniq.append(f)
    return uniq
