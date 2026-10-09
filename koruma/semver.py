"""Kütüphane sürümlerini karşılaştırmak için küçük, hoşgörülü bir sürüm aracı.

Tam bir SemVer uygulaması değildir; "3.4.1", "1.8.0", "4.17.21",
"3.0.0-rc.1" gibi tipik JS kütüphane sürümlerini doğru sıralar.
Ön sürümler (pre-release, ör. -rc.1) aynı sayısal sürümden küçüktür.
"""
from __future__ import annotations

import re

_NUM = re.compile(r"\d+")


def _parts(v: str):
    v = v.strip().lstrip("vV")
    main, _, pre = v.partition("-")
    nums = [int(x) for x in main.split(".") if x.isdigit() or _NUM.fullmatch(x)]
    # Eksik bileşenleri 0 kabul et
    while len(nums) < 3:
        nums.append(0)
    return nums[:4], pre


def compare(a: str, b: str) -> int:
    """a<b ise -1, a==b ise 0, a>b ise 1 döndürür."""
    na, pa = _parts(a)
    nb, pb = _parts(b)
    for x, y in zip(na + [0] * (len(nb) - len(na)), nb + [0] * (len(na) - len(nb))):
        if x != y:
            return -1 if x < y else 1
    # Sayısal kısımlar eşit: ön sürüm olan daha küçüktür
    if pa and not pb:
        return -1
    if pb and not pa:
        return 1
    if pa != pb:
        return -1 if pa < pb else 1
    return 0


def lt(a: str, b: str) -> bool:
    return compare(a, b) < 0


def gte(a: str, b: str) -> bool:
    return compare(a, b) >= 0


def gt(a: str, b: str) -> bool:
    return compare(a, b) > 0


def in_range(version: str, atOrAbove=None, below=None, above=None) -> bool:
    """Sürümün verilen aralıkta (açık güvenlik açığı aralığı) olup olmadığı."""
    try:
        if atOrAbove is not None and not gte(version, atOrAbove):
            return False
        if above is not None and not gt(version, above):
            return False
        if below is not None and not lt(version, below):
            return False
    except (ValueError, TypeError):
        return False
    return True
