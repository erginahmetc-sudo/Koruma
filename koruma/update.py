"""Savunmasız bileşen (CVE) veritabanını Retire.js'ten günceller.

Retire.js'in kamuya açık jsrepository verisini indirir, Koruma'nın
js_vulns.json şemasına dönüştürür ve mevcut veritabanıyla BİRLEŞTİRİR:
elle hazırlanmış (Türkçe özetli) kütüphaneler korunur; eksik olanlar
Retire.js'ten eklenir. Böylece kapsam güncel ve geniş kalır.
"""
from __future__ import annotations

import json
from pathlib import Path

RETIRE_URLS = [
    "https://raw.githubusercontent.com/RetireJS/retire.js/master/repository/jsrepository-master.json",
    "https://raw.githubusercontent.com/RetireJS/retire.js/master/repository/jsrepository.json",
]
DB_PATH = Path(__file__).resolve().parent / "data" / "js_vulns.json"
SEV_MAP = {"low": "LOW", "medium": "MEDIUM", "high": "HIGH", "critical": "CRITICAL"}


def _fetch(timeout=30) -> dict:
    import requests
    last = None
    for url in RETIRE_URLS:
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as e:  # noqa
            last = e
    raise RuntimeError(f"Retire.js verisi indirilemedi: {last}")


def _convert_entry(entry: dict) -> dict | None:
    ex = entry.get("extractors", {})
    extractors = []
    for key in ("uri", "filename", "filecontent"):
        for pat in ex.get(key, []):
            if "§§version§§" in pat:
                extractors.append(pat)
    if not extractors:
        return None  # sürüm tespiti yapılamayan kütüphaneyi atla

    vulns = []
    for v in entry.get("vulnerabilities", []):
        ident = v.get("identifiers", {})
        ids = list(ident.get("CVE", [])) or list(ident.get("githubID", [])) or []
        summary = v.get("summary") or ident.get("summary") or (v.get("info", [""])[0] if v.get("info") else "")
        severity = SEV_MAP.get((v.get("severity") or "medium").lower(), "MEDIUM")
        # Sürüm sınırları "ranges" altında (ya da bazı sürümlerde doğrudan vuln üzerinde)
        ranges = v.get("ranges") or [v]
        for rng_src in ranges:
            rng = {"ids": ids, "severity": severity,
                   "summary": (summary or "Bilinen güvenlik açığı.")[:300]}
            for bound in ("atOrAbove", "below", "above"):
                if rng_src.get(bound):
                    rng[bound] = rng_src[bound]
            if "below" in rng or "above" in rng or "atOrAbove" in rng:
                vulns.append(rng)
    if not vulns:
        return None
    return {"extractors": extractors, "vulns": vulns}


def update_db(log=print) -> tuple[int, int]:
    """Veritabanını günceller. (eklenen_veya_güncellenen, toplam) döndürür."""
    log("» Retire.js zafiyet veritabanı indiriliyor…")
    retire = _fetch()
    log(f"  {len(retire)} kütüphane alındı; dönüştürülüyor…")

    with open(DB_PATH, encoding="utf-8") as fh:
        current = json.load(fh)
    libs = current.setdefault("libraries", {})
    curated = set(libs.keys())  # elle hazırlanmış kütüphaneleri koru

    added = 0
    for name, entry in retire.items():
        if not isinstance(entry, dict) or name in curated:
            continue
        converted = _convert_entry(entry)
        if converted:
            libs[name] = converted
            added += 1

    current.setdefault("_meta", {})["retire_sync"] = True
    with open(DB_PATH, "w", encoding="utf-8") as fh:
        json.dump(current, fh, ensure_ascii=False, indent=2)
    log(f"  {added} yeni kütüphane eklendi; elle hazırlanmış {len(curated)} kütüphane korundu.")
    return added, len(libs)


if __name__ == "__main__":
    update_db()
