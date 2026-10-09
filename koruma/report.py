from __future__ import annotations

import html
import json
from collections import Counter
from datetime import datetime

from koruma.models import Severity
from koruma.scanner import ScanResult

COLORS = {
    "KRİTİK": "\033[97;41m", "YÜKSEK": "\033[91m", "ORTA": "\033[93m",
    "DÜŞÜK": "\033[94m", "BİLGİ": "\033[90m",
}
RESET = "\033[0m"
BOLD = "\033[1m"


def _counts(result: ScanResult) -> Counter:
    return Counter(f.severity.label for f in result.findings)


def to_text(result: ScanResult, color: bool = True) -> str:
    def c(code, s):
        return f"{code}{s}{RESET}" if color else s

    out = []
    out.append(c(BOLD, f"\n╔══ Koruma Güvenlik Raporu ══╗"))
    out.append(f"Hedef     : {result.base_url}")
    out.append(f"Tarih     : {datetime.now():%Y-%m-%d %H:%M}")
    out.append(f"Taranan   : {result.pages_crawled} sayfa, {result.forms_found} form, "
               f"{result.requests_made} istek, {result.duration:.1f} sn")

    counts = _counts(result)
    summary = "  ".join(
        c(COLORS[s.label], f"{s.label}: {counts.get(s.label, 0)}")
        for s in sorted(Severity, reverse=True)
    )
    out.append(f"Özet      : {summary}")

    if result.errors:
        out.append(c(COLORS["ORTA"], "\nUyarılar:"))
        for e in result.errors:
            out.append(f"  - {e}")

    if not result.findings:
        out.append(c(COLORS["BİLGİ"], "\n✓ Belirtilen kontrollerde bulgu yok."))
    else:
        out.append("")
        for i, f in enumerate(result.findings, 1):
            tag = c(COLORS[f.severity.label], f" {f.severity.label} ")
            out.append(f"{BOLD if color else ''}{i}. [{tag}{RESET if color else ''}{BOLD if color else ''}] {f.title}{RESET if color else ''}")
            out.append(f"   URL    : {f.url}")
            out.append(f"   Sorun  : {f.description}")
            out.append(f"   Çözüm  : {f.recommendation}")
            if f.evidence:
                out.append(f"   Kanıt  : {f.evidence}")
            out.append("")
    return "\n".join(out)


def to_json(result: ScanResult) -> str:
    counts = _counts(result)
    return json.dumps({
        "target": result.base_url,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stats": {
            "pages_crawled": result.pages_crawled,
            "forms_found": result.forms_found,
            "requests_made": result.requests_made,
            "duration_seconds": round(result.duration, 2),
        },
        "summary": {s.label: counts.get(s.label, 0) for s in sorted(Severity, reverse=True)},
        "errors": result.errors,
        "findings": [f.to_dict() for f in result.findings],
    }, ensure_ascii=False, indent=2)


def to_html(result: ScanResult) -> str:
    counts = _counts(result)
    css_color = {"KRİTİK": "#7f1d1d", "YÜKSEK": "#dc2626", "ORTA": "#d97706",
                 "DÜŞÜK": "#2563eb", "BİLGİ": "#6b7280"}
    rows = []
    for f in result.findings:
        col = css_color[f.severity.label]
        rows.append(f"""
        <div class="card" style="border-left-color:{col}">
          <div class="head"><span class="badge" style="background:{col}">{f.severity.label}</span>
            <strong>{html.escape(f.title)}</strong></div>
          <div class="url"><a href="{html.escape(f.url)}">{html.escape(f.url)}</a></div>
          <p><b>Sorun:</b> {html.escape(f.description)}</p>
          <p><b>Çözüm:</b> {html.escape(f.recommendation)}</p>
          {f'<pre>{html.escape(f.evidence)}</pre>' if f.evidence else ''}
        </div>""")
    summary = "".join(
        f'<span class="pill" style="background:{css_color[s.label]}">{s.label}: {counts.get(s.label, 0)}</span>'
        for s in sorted(Severity, reverse=True)
    )
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Koruma Raporu - {html.escape(result.base_url)}</title>
<style>
  body{{font-family:system-ui,Segoe UI,Roboto,sans-serif;margin:0;background:#f8fafc;color:#111827}}
  header{{background:#0f172a;color:#fff;padding:24px}}
  header h1{{margin:0 0 6px;font-size:20px}} .muted{{color:#94a3b8;font-size:14px}}
  .wrap{{max-width:860px;margin:0 auto;padding:16px}}
  .pill,.badge{{color:#fff;border-radius:999px;padding:3px 10px;font-size:12px;font-weight:600}}
  .summary{{margin:16px 0;display:flex;gap:8px;flex-wrap:wrap}}
  .card{{background:#fff;border:1px solid #e5e7eb;border-left-width:5px;border-radius:8px;padding:14px;margin:12px 0}}
  .head{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
  .url{{font-size:13px;margin-bottom:8px;word-break:break-all}} p{{margin:6px 0;font-size:14px}}
  pre{{background:#f1f5f9;padding:8px;border-radius:6px;overflow:auto;font-size:12px}}
</style></head><body>
<header><div class="wrap"><h1>Koruma Güvenlik Raporu</h1>
<div class="muted">{html.escape(result.base_url)} · {datetime.now():%Y-%m-%d %H:%M} ·
{result.pages_crawled} sayfa · {result.requests_made} istek</div></div></header>
<div class="wrap"><div class="summary">{summary}</div>
{''.join(rows) or '<div class="card">Belirtilen kontrollerde bulgu yok.</div>'}
<p class="muted">Koruma, kendi sitenizi test etmeniz içindir. Çıktı bir güvenlik garantisi değildir.</p>
</div></body></html>"""
