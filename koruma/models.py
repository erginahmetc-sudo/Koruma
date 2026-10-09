from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import IntEnum


class Severity(IntEnum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @property
    def label(self) -> str:
        return {
            Severity.INFO: "BİLGİ",
            Severity.LOW: "DÜŞÜK",
            Severity.MEDIUM: "ORTA",
            Severity.HIGH: "YÜKSEK",
            Severity.CRITICAL: "KRİTİK",
        }[self]


@dataclass
class Finding:
    check: str
    title: str
    severity: Severity
    url: str
    description: str
    recommendation: str
    evidence: str = ""

    def key(self) -> tuple:
        return (self.check, self.title, self.url)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.label
        return d


@dataclass
class Form:
    action: str
    method: str
    inputs: dict[str, str] = field(default_factory=dict)
    page_url: str = ""
