from __future__ import annotations

#=========================كود التذييل============================

from reportlab.lib import colors
from reportlab.pdfgen import canvas

class FooterCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)

        for page in self.pages:
            self.__dict__.update(page)

            # التذييل في الصفحة الأخيرة فقط
            if self._pageNumber == page_count:
                self.setFont(FONT_NAME, 10)

                # لون رمادي باهت
                self.setFillColorRGB(0.7, 0.7, 0.7)

                self.drawCentredString(
                    landscape(A4)[0] / 2,
                    25,
                    _rtl("المهندس المالي : عزت العصعص | أتمتة الأعمال بالذكاء الاصطناعي")
                )

                self.drawCentredString(
                    landscape(A4)[0] / 2,
                    12,
                    _rtl("للتواصل : 777884468")
                )
            super().showPage()

        super().save()




#============================================================


import os
from datetime import datetime
from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:
    arabic_reshaper = None
    get_display = None


PROGRAM_NAME = "نظام العصعص لتحليل المبيعات"
PROGRAM_SUBTITLE = "AL-osos Professional Sales Analyzer 2026"

#===============
def _register_arabic_font() -> str:
    pdfmetrics.registerFont(
        TTFont("ArabicFont", "arial.ttf")
    )
    return "ArabicFont"


FONT_NAME = _register_arabic_font()

#=====================

def _rtl(value) -> str:
    text = "" if pd.isna(value) else str(value)
    if arabic_reshaper and get_display:
        return get_display(arabic_reshaper.reshape(text))
    return text


def _money(value) -> str:
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _percent(value) -> str:
    try:
        return f"{float(value):,.2f}%"
    except (TypeError, ValueError):
        return str(value)


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ArabicTitle",
            parent=base["Title"],
            fontName=FONT_NAME,
            fontSize=24,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1E3A5F"),
            leading=34,
        ),
        "subtitle": ParagraphStyle(
            "ArabicSubtitle",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
            leading=18,
        ),
        "heading": ParagraphStyle(
            "ArabicHeading",
            parent=base["Heading2"],
            fontName=FONT_NAME,
            fontSize=16,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#1E3A5F"),
            leading=24,
        ),
        "normal": ParagraphStyle(
            "ArabicNormal",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=10,
            alignment=TA_RIGHT,
            leading=16,
        ),
    }


def _paragraph(text, style):
    return Paragraph(_rtl(text), style)


def _table_from_frame(frame: pd.DataFrame, max_rows: int = 18) -> Table:
    shown = frame.head(max_rows).copy()
    if shown.empty:
        shown = pd.DataFrame({"البيان": ["لا توجد بيانات"]})

    for column in shown.columns:
        if column in ["الحالي", "السابق", "الفرق", "القيمة"]:
            shown[column] = shown[column].map(_money)
        elif column == "النسبة":
            shown[column] = shown[column].map(_percent)

    data = [[_rtl(column) for column in shown.columns]]
    data.extend([[_rtl(value) for value in row] for row in shown.astype(str).values.tolist()])

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _metrics_frame(metrics: dict) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"المؤشر": "إجمالي المبيعات الحالية", "القيمة": _money(metrics["current_total"])},
            {"المؤشر": "إجمالي المبيعات السابقة", "القيمة": _money(metrics["previous_total"])},
            {"المؤشر": "إجمالي الفرق", "القيمة": _money(metrics["difference"])},
            {"المؤشر": "نسبة النمو", "القيمة": _percent(metrics["growth"])},
            {"المؤشر": "عدد العملاء", "القيمة": metrics["customers_count"]},
            {"المؤشر": "عدد المنتجات", "القيمة": metrics["products_count"]},
            {"المؤشر": "عدد المناديب", "القيمة": metrics["representatives_count"]},
            {"المؤشر": "عدد الفروع", "القيمة": metrics["branches_count"]},
        ]
    )


def _add_section(story, title: str, frame: pd.DataFrame, styles: dict, max_rows: int = 18):
    story.append(_paragraph(title, styles["heading"]))
    story.append(Spacer(1, 0.25 * cm))
    story.append(_table_from_frame(frame, max_rows=max_rows))
    story.append(Spacer(1, 0.5 * cm))


def export_to_pdf(
    metrics: dict,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    representatives: pd.DataFrame,
    branches: pd.DataFrame,
    insights: pd.DataFrame,
) -> BytesIO:
    """إنشاء تقرير PDF عربي احترافي باستخدام ReportLab."""
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )
    styles = _styles()
    story = []

    story.append(Spacer(1, 2.0 * cm))
    story.append(_paragraph(PROGRAM_NAME, styles["title"]))
    story.append(_paragraph(PROGRAM_SUBTITLE, styles["subtitle"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(_paragraph(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["subtitle"]))
    story.append(PageBreak())

    story.append(_paragraph("ملخص تنفيذي", styles["heading"]))
    story.append(
        _paragraph(
            "يعرض هذا التقرير مؤشرات الأداء الرئيسية وتحليل العملاء والمنتجات والمناديب والفروع وفق البيانات المرفوعة من ملف Excel.",
            styles["normal"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))
    story.append(_table_from_frame(_metrics_frame(metrics), max_rows=20))
    story.append(Spacer(1, 0.5 * cm))

    _add_section(story, "مركز ذكاء الأعمال", insights, styles, max_rows=12)
    story.append(PageBreak())
    _add_section(story, "تحليل العملاء", customers, styles)
    _add_section(story, "تحليل المنتجات", products, styles)
    story.append(PageBreak())
    _add_section(story, "تحليل المناديب", representatives, styles)
    _add_section(story, "تحليل الفروع", branches, styles)

    #============================================================

    #=============================================================

    document.build(
        story,
        canvasmaker=FooterCanvas
    )
    output.seek(0)
    return output

