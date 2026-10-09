"""Merkezi sır (gizli anahtar/token) tarayıcı.

Kurallar gitleaks projesinden türetilmiştir (koruma/data/secret_rules.json).
disclosure ve jsrecon kontrolleri bu modülü paylaşır.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from json import load
from pathlib import Path

from koruma.models import Severity

_SEV = {"LOW": Severity.LOW, "MEDIUM": Severity.MEDIUM, "HIGH": Severity.HIGH,
        "CRITICAL": Severity.CRITICAL}
_PATH = Path(__file__).resolve().parent / "data" / "secret_rules.json"


@dataclass
class Rule:
    name: str
    severity: Severity
    rx: "re.Pattern"


@lru_cache(maxsize=1)
def _rules() -> list[Rule]:
    with open(_PATH, encoding="utf-8") as fh:
        data = load(fh)
    rules = []
    for r in data["rules"]:
        try:
            rx = re.compile(r["regex"], re.I if r.get("ci") else 0)
        except re.error:
            continue
        rules.append(Rule(r["name"], _SEV.get(r["severity"], Severity.MEDIUM), rx))
    return rules


def _value(m) -> str:
    if m.re.groups >= 1 and m.group(1):
        return m.group(1)
    return m.group(0)


def scan(text: str):
    """(name, value, severity) üçlülerini döndürür (yinelenenler elenmiş)."""
    seen = set()
    out = []
    for rule in _rules():
        for m in rule.rx.finditer(text):
            val = _value(m)
            key = (rule.name, val)
            if key in seen:
                continue
            seen.add(key)
            out.append((rule.name, val, rule.severity))
    return out


def redact(val: str) -> str:
    if len(val) <= 12:
        return val[:3] + "…"
    return val[:8] + "…" + val[-4:]
