from __future__ import annotations
import csv, io, json, os
from pathlib import Path
from backend.database import Database

def export_json(db: Database, scan_id: int) -> bytes:
    scan=db.get_scan(scan_id)
    if not scan: raise KeyError("scan not found")
    payload={"scan":scan,"signal":db.get_signal(scan_id),"evidence":db.evidence_for_scan(scan_id)}
    return json.dumps(payload,ensure_ascii=False,indent=2).encode("utf-8")

def export_csv(db: Database, scan_id: int) -> bytes:
    rows=db.evidence_for_scan(scan_id)
    out=io.StringIO()
    w=csv.writer(out)
    w.writerow(["source","external_id","title","year","doi","url","authors","affiliations"])
    for r in rows:
        w.writerow([
            r["source_code"],r["external_id"],r["title"],r["year"] or "",
            r["doi"] or "",r["url"] or "","; ".join(r["authors"]),"; ".join(r["affiliations"])
        ])
    return ("\ufeff"+out.getvalue()).encode("utf-8")

def _shape_fa(text: str) -> str:
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)

def export_pdf(db: Database, scan_id: int) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    scan=db.get_scan(scan_id)
    signal=db.get_signal(scan_id)
    evidence=db.evidence_for_scan(scan_id)
    if not scan or not signal: raise KeyError("scan not found")

    font="Helvetica"
    candidates=[
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansArabic-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("EHFont",path))
                font="EHFont";break
            except Exception:
                pass

    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=36,leftMargin=36,topMargin=36,bottomMargin=36)
    styles=getSampleStyleSheet()
    title=ParagraphStyle("faTitle",parent=styles["Title"],fontName=font,fontSize=18,leading=26,alignment=2)
    body=ParagraphStyle("faBody",parent=styles["BodyText"],fontName=font,fontSize=9,leading=15,alignment=2)
    small=ParagraphStyle("small",parent=body,fontSize=7,leading=11)
    story=[
        Paragraph(_shape_fa("گزارش پایش افق اخلاقی"),title),
        Spacer(1,12),
        Paragraph(_shape_fa(f"موضوع: {scan['query']}"),body),
        Paragraph(_shape_fa(f"امتیاز سیگنال: {signal['signal_score']} / 100"),body),
        Paragraph(_shape_fa(f"اولویت: {signal['priority']}"),body),
        Paragraph(_shape_fa(f"بلوغ فناوری: {signal['maturity']['stage']}"),body),
        Paragraph(_shape_fa(f"شدت اخلاقی: {signal['ethics']['intensity']}"),body),
        Paragraph(_shape_fa(f"ارتباط با ایران: {signal['iran']['level']}"),body),
        Paragraph(_shape_fa(f"روند: {signal['trend']['direction']}"),body),
        Spacer(1,12),
    ]
    data=[
        [_shape_fa("شاخص"),_shape_fa("مقدار")],
        [_shape_fa("روند"),str(signal["trend"]["score"])],
        [_shape_fa("فعالیت بالینی"),str(signal["clinical_activity_score"])],
        [_shape_fa("پیچیدگی اخلاقی"),str(signal["ethics"]["score"])],
        [_shape_fa("ارتباط ایران"),str(signal["iran"]["score"])],
        [_shape_fa("نوظهوری"),str(signal["novelty_score"])],
    ]
    t=Table(data,colWidths=[180,180],hAlign="RIGHT")
    t.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),font),
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17324d")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#ccd7e2")),
        ("ALIGN",(0,0),(-1,-1),"RIGHT"),
        ("PADDING",(0,0),(-1,-1),6),
    ]))
    story += [t,Spacer(1,18),Paragraph(_shape_fa("شواهد بازیابی‌شده"),title),Spacer(1,8)]
    for r in evidence[:50]:
        story.append(Paragraph(f"<b>{r['source_code']}</b> - {r['title']}",small))
        meta=f"{r['year'] or ''} | {r['doi'] or r['external_id']} | {r['url'] or ''}"
        story.append(Paragraph(meta,small))
        story.append(Spacer(1,6))
    doc.build(story)
    return buf.getvalue()
