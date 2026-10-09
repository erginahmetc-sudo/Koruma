"""Tarama sonucundan (ScanResult veya JSON) PDF rapor üretir.

reportlab gerektirir. Komut satırından:
    python -m koruma.pdfreport <girdi.json> <cikti.pdf>
(masaüstü uygulaması bu yolu kullanır) ya da program içinden build_pdf().
"""
from __future__ import annotations

import json
import sys

SEV_COLOR = {
    "KRİTİK": "#b91c1c", "YÜKSEK": "#ea580c", "ORTA": "#ca8a04",
    "DÜŞÜK": "#2563eb", "BİLGİ": "#6b7280",
}
SEV_ORDER = ["KRİTİK", "YÜKSEK", "ORTA", "DÜŞÜK", "BİLGİ"]


def build_pdf(data: dict, out_path: str) -> str:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (HRFlowable, Paragraph, SimpleDocTemplate,
                                    Spacer, Table, TableStyle)

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("kh1", parent=styles["Heading1"], fontSize=18, spaceAfter=4)
    meta = ParagraphStyle("kmeta", parent=styles["Normal"], fontSize=9, textColor=colors.grey)
    title_s = ParagraphStyle("ktitle", parent=styles["Heading3"], fontSize=11, spaceAfter=2, spaceBefore=6)
    body_s = ParagraphStyle("kbody", parent=styles["Normal"], fontSize=9, leading=13, alignment=TA_LEFT)
    label_s = ParagraphStyle("klabel", parent=body_s, textColor=colors.HexColor("#0ea5e9"))
    ev_s = ParagraphStyle("kev", parent=body_s, fontName="Courier", fontSize=8,
                          textColor=colors.HexColor("#334155"), backColor=colors.HexColor("#f1f5f9"))

    def esc(s):
        return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    doc = SimpleDocTemplate(out_path, pagesize=A4, title="Koruma Güvenlik Raporu",
                            leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm)
    story = []
    story.append(Paragraph("🛡 Koruma Güvenlik Raporu", h1))
    st = data.get("stats", {})
    story.append(Paragraph(
        f"Hedef: {esc(data.get('target'))} &nbsp;·&nbsp; {esc(data.get('generated_at'))}<br/>"
        f"{st.get('pages_crawled', 0)} sayfa · {st.get('forms_found', 0)} form · "
        f"{st.get('requests_made', 0)} istek · {st.get('duration_seconds', 0)} sn", meta))
    story.append(Spacer(1, 6))

    # Özet tablosu
    summary = data.get("summary", {})
    cells = [[Paragraph(f"<b>{s}</b>", body_s), str(summary.get(s, 0))] for s in SEV_ORDER]
    tbl = Table([["Önem", "Adet"]] + cells, colWidths=[40 * mm, 20 * mm])
    style = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
             ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
             ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
             ("FONTSIZE", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 3),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    for i, s in enumerate(SEV_ORDER, start=1):
        style.append(("TEXTCOLOR", (0, i), (0, i), colors.HexColor(SEV_COLOR[s])))
    tbl.setStyle(TableStyle(style))
    story.append(tbl)
    story.append(Spacer(1, 10))

    findings = data.get("findings", [])
    if not findings:
        story.append(Paragraph("Belirtilen kontrollerde bulgu bulunamadı.", body_s))
    for i, f in enumerate(findings, 1):
        col = SEV_COLOR.get(f.get("severity"), "#334155")
        story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#e2e8f0")))
        story.append(Paragraph(
            f'<font color="{col}"><b>[{esc(f.get("severity"))}]</b></font> '
            f'{i}. {esc(f.get("title"))}', title_s))
        story.append(Paragraph(f'<font color="#2563eb">{esc(f.get("url"))}</font>', meta))
        story.append(Paragraph(f'<b>Sorun:</b> {esc(f.get("description"))}', body_s))
        story.append(Paragraph(f'<b>Çözüm:</b> {esc(f.get("recommendation"))}', label_s))
        if f.get("evidence"):
            story.append(Paragraph(f'Kanıt: {esc(f.get("evidence"))}', ev_s))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Koruma yalnızca kendi sitenizi test etmeniz içindir ve bir güvenlik "
                           "garantisi değildir.", meta))
    doc.build(story)
    return out_path


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) != 2:
        print("Kullanım: python -m koruma.pdfreport <girdi.json> <cikti.pdf>", file=sys.stderr)
        return 1
    with open(argv[0], encoding="utf-8") as fh:
        data = json.load(fh)
    build_pdf(data, argv[1])
    print(argv[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
