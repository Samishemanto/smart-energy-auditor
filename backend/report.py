"""PDF report generation for Smart Energy Auditor."""
import io
from datetime import datetime
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Brand colours
TEAL   = colors.HexColor("#00C9B8")
BLUE   = colors.HexColor("#1D4ED8")
DARK   = colors.HexColor("#060B17")
PANEL  = colors.HexColor("#0C1525")
BORDER = colors.HexColor("#1A2840")
TEXT   = colors.HexColor("#CBD5E1")
MUTED  = colors.HexColor("#4B6280")
WHITE  = colors.white
GREEN  = colors.HexColor("#10B981")
RED    = colors.HexColor("#EF4444")
AMBER  = colors.HexColor("#F59E0B")


def _style(name, **kwargs) -> ParagraphStyle:
    base = getSampleStyleSheet()["Normal"]
    return ParagraphStyle(name, parent=base, **kwargs)


def generate_pdf_report(user_email: str, user_name: str, bills: list, stats: dict) -> bytes:
    """Return PDF bytes for the user's energy report."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=14*mm, bottomMargin=14*mm,
    )

    title_style  = _style("Title",  fontSize=22, textColor=WHITE,  fontName="Helvetica-Bold",  spaceAfter=4)
    sub_style    = _style("Sub",    fontSize=10, textColor=MUTED,  fontName="Helvetica",        spaceAfter=12)
    head_style   = _style("Head",   fontSize=13, textColor=TEAL,   fontName="Helvetica-Bold",  spaceAfter=6, spaceBefore=14)
    body_style   = _style("Body",   fontSize=9,  textColor=TEXT,   fontName="Helvetica",        leading=14)
    label_style  = _style("Label",  fontSize=7,  textColor=MUTED,  fontName="Helvetica",        spaceAfter=2)
    value_style  = _style("Value",  fontSize=16, textColor=WHITE,  fontName="Helvetica-Bold",  spaceAfter=0)
    footer_style = _style("Footer", fontSize=7,  textColor=MUTED,  fontName="Helvetica",        alignment=TA_CENTER)

    story = []

    # ── Header ──
    story.append(Paragraph("⚡ Smart Energy Auditor", title_style))
    story.append(Paragraph(f"Energy Report · {user_name or user_email} · {datetime.now().strftime('%d %B %Y')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=10))

    # ── KPI summary row ──
    n = stats.get("total_bills", 0)
    total_spend  = stats.get("total_spend", 0)
    avg_kwh      = stats.get("avg_monthly_kwh", 0)
    total_carbon = stats.get("total_carbon_kg", 0)

    kpi_data = [
        [Paragraph("BILLS ANALYSED",   label_style), Paragraph("TOTAL SPEND",      label_style),
         Paragraph("AVG USAGE / BILL", label_style), Paragraph("TOTAL CO₂",        label_style)],
        [Paragraph(str(n),             value_style), Paragraph(f"£{total_spend:,.2f}", value_style),
         Paragraph(f"{avg_kwh:.0f} kWh", value_style), Paragraph(f"{total_carbon:.1f} kg", value_style)],
    ]
    kpi_table = Table(kpi_data, colWidths=["25%", "25%", "25%", "25%"])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), PANEL),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [PANEL, PANEL]),
        ("BOX",          (0, 0), (-1, -1), 0.8, BORDER),
        ("INNERGRID",    (0, 0), (-1, -1), 0.4, BORDER),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # ── Bill table ──
    story.append(Paragraph("Bill History", head_style))

    headers = ["#", "Provider", "Date", "Amount (£)", "Usage (kWh)", "CO₂ (kg)", "Tariff"]
    th_style = _style("TH", fontSize=7, textColor=MUTED, fontName="Helvetica-Bold")
    td_style = _style("TD", fontSize=8, textColor=TEXT,  fontName="Helvetica")
    td_num   = _style("TDN", fontSize=8, textColor=WHITE, fontName="Helvetica-Bold", alignment=TA_RIGHT)

    rows = [[Paragraph(h, th_style) for h in headers]]
    for b in sorted(bills, key=lambda x: x.id):
        rows.append([
            Paragraph(str(b.id),                               td_style),
            Paragraph(b.provider or "Unknown",                 td_style),
            Paragraph(b.bill_date or "—",                      td_style),
            Paragraph(f"£{b.amount_due:.2f}" if b.amount_due else "—", td_num),
            Paragraph(str(b.usage_kwh) if b.usage_kwh else "—",        td_num),
            Paragraph(f"{b.carbon_kg:.1f}" if b.carbon_kg else "—",    td_num),
            Paragraph((b.tariff_name or "—")[:22],             td_style),
        ])

    bill_table = Table(rows, colWidths=[10*mm, 38*mm, 26*mm, 22*mm, 22*mm, 18*mm, 34*mm])
    bill_table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  DARK),
        ("BACKGROUND",     (0, 1), (-1, -1), PANEL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL, colors.HexColor("#0A1018")]),
        ("BOX",            (0, 0), (-1, -1), 0.6, BORDER),
        ("LINEBELOW",      (0, 0), (-1, 0),  1.0, TEAL),
        ("INNERGRID",      (0, 1), (-1, -1), 0.3, BORDER),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(bill_table)
    story.append(Spacer(1, 12))

    # ── Carbon section ──
    if total_carbon > 0:
        story.append(Paragraph("Carbon Footprint", head_style))
        uk_avg = 3100 * 0.197
        trees  = round(total_carbon / 21.7, 1)
        km     = round(total_carbon / 0.17)
        pct    = round((total_carbon / (n or 1) * 12 - uk_avg) / uk_avg * 100, 1) if n else 0
        pct_word = "above" if pct > 0 else "below"
        story.append(Paragraph(
            f"Your {n} bill(s) generated <b>{total_carbon:.1f} kg CO₂</b> — estimated annual rate is "
            f"<b>{total_carbon / (n or 1) * 12:.0f} kg/yr</b>, {abs(pct):.1f}% {pct_word} the UK household average "
            f"({uk_avg:.0f} kg/yr). Equivalent to driving <b>{km:,} km</b> or planting "
            f"<b>{trees} trees</b> to offset.",
            body_style,
        ))
        story.append(Spacer(1, 8))

    # ── Footer ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=16, spaceAfter=8))
    story.append(Paragraph(
        f"Generated by Smart Energy Auditor · {datetime.now().strftime('%d %B %Y %H:%M')} · "
        f"Carbon factor: 0.197 kg CO₂/kWh (UK National Grid 2024)",
        footer_style,
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()
