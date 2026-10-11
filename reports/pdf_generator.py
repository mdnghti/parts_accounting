from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from db.connection import get_resource_dir
from models.document import Document
from models.part import Part

FONT_REGISTERED = False
CYRILLIC_FONT = "Helvetica"  # За замовчуванням


def ensure_cyrillic_font() -> str:
    """Реєстрація TrueType шрифту з підтримкою українських символів."""
    global FONT_REGISTERED, CYRILLIC_FONT
    if FONT_REGISTERED:
        return CYRILLIC_FONT

    font_candidates = [
        get_resource_dir() / "resources" / "fonts" / "DejaVuSans.ttf",
        Path("/usr/share/fonts/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]

    for candidate in font_candidates:
        if candidate.exists():
            try:
                pdfmetrics.registerFont(TTFont("CustomCyrillic", str(candidate)))
                CYRILLIC_FONT = "CustomCyrillic"
                FONT_REGISTERED = True
                return CYRILLIC_FONT
            except Exception:
                continue

    FONT_REGISTERED = True
    return CYRILLIC_FONT


def export_stock_to_pdf(parts: List[Part], output_path: Path | str) -> str:
    """Генерація PDF-звіту: Залишки на складі."""
    font_name = ensure_cyrillic_font()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=25,
        bottomMargin=25,
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        fontName=font_name,
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1F497D"),
        alignment=1,  # Center
    )
    sub_style = ParagraphStyle(
        "SubStyle",
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#595959"),
        alignment=1,
    )
    cell_style = ParagraphStyle(
        "CellStyle",
        fontName=font_name,
        fontSize=8,
        leading=10,
    )
    header_style = ParagraphStyle(
        "HeaderStyle",
        fontName=font_name,
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1,
    )

    elements.append(Paragraph("ЗВІТ: ЗАЛИШКИ АВТОЗАПЧАСТИН НА СКЛАДІ", title_style))
    elements.append(Paragraph(f"Дата формування: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", sub_style))
    elements.append(Spacer(1, 15))

    # Заголовки таблиці
    headers = [
        "№",
        "Артикул",
        "Найменування запчастини",
        "Категорія",
        "Ціна (грн)",
        "Залишок",
        "Мін.",
        "Од.",
        "Сума (грн)",
        "Статус",
    ]
    table_data = [[Paragraph(h, header_style) for h in headers]]

    total_qty = 0
    total_amount = 0.0

    table_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F497D")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
    ]

    for idx, part in enumerate(parts, 1):
        row_amount = round(part.price * part.stock_quantity, 2)
        total_qty += part.stock_quantity
        total_amount += row_amount
        status = "ДЕФІЦИТ" if part.is_low_stock else "В нормі"

        row = [
            Paragraph(str(idx), cell_style),
            Paragraph(part.part_number, cell_style),
            Paragraph(part.name, cell_style),
            Paragraph(part.category_name or "—", cell_style),
            Paragraph(f"{part.price:.2f}", cell_style),
            Paragraph(str(part.stock_quantity), cell_style),
            Paragraph(str(part.min_stock_quantity), cell_style),
            Paragraph(part.unit, cell_style),
            Paragraph(f"{row_amount:.2f}", cell_style),
            Paragraph(status, cell_style),
        ]
        table_data.append(row)

        if part.is_low_stock:
            # Червонувате підсвічування рядка дефіциту
            table_styles.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#FFEEEE")))

    # Підсумковий рядок
    tot_row_idx = len(table_data)
    table_data.append(
        [
            "",
            "",
            Paragraph("<b>РАЗОМ ПО СКЛАДУ:</b>", cell_style),
            "",
            "",
            Paragraph(f"<b>{total_qty}</b>", cell_style),
            "",
            "",
            Paragraph(f"<b>{total_amount:.2f}</b>", cell_style),
            "",
        ]
    )
    table_styles.append(("BACKGROUND", (0, tot_row_idx), (-1, tot_row_idx), colors.HexColor("#D9E1F2")))
    table_styles.append(("LINEABOVE", (0, tot_row_idx), (-1, tot_row_idx), 1, colors.black))

    col_widths = [25, 65, 230, 110, 65, 50, 40, 35, 75, 55]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(table_styles))
    elements.append(table)

    doc.build(elements)
    return str(Path(output_path).resolve())


def export_movement_to_pdf(documents: List[Document], output_path: Path | str) -> str:
    """Генерація PDF-звіту: Рух товарів за період."""
    font_name = ensure_cyrillic_font()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=25,
        bottomMargin=25,
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        fontName=font_name,
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1F497D"),
        alignment=1,
    )
    sub_style = ParagraphStyle(
        "SubStyle",
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#595959"),
        alignment=1,
    )
    cell_style = ParagraphStyle("CellStyle", fontName=font_name, fontSize=8, leading=10)
    header_style = ParagraphStyle("HeaderStyle", fontName=font_name, fontSize=8, leading=10, textColor=colors.white, alignment=1)

    elements.append(Paragraph("ЗВІТ: РУХ ТОВАРІВ ЗА ПЕРІОД", title_style))
    elements.append(Paragraph(f"Дата формування: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", sub_style))
    elements.append(Spacer(1, 15))

    headers = [
        "№ документу",
        "Тип операції",
        "Дата",
        "Контрагент",
        "Артикул",
        "Найменування запчастини",
        "К-сть",
        "Ціна (грн)",
        "Сума (грн)",
    ]
    table_data = [[Paragraph(h, header_style) for h in headers]]

    total_qty = 0
    total_amount = 0.0

    for d in documents:
        for it in d.items:
            total_qty += it.quantity
            total_amount += it.total_price

            row = [
                Paragraph(d.doc_number, cell_style),
                Paragraph(d.doc_type_ukr, cell_style),
                Paragraph(d.doc_date, cell_style),
                Paragraph(d.counterparty_name, cell_style),
                Paragraph(it.part_number or "—", cell_style),
                Paragraph(it.part_name or "—", cell_style),
                Paragraph(str(it.quantity), cell_style),
                Paragraph(f"{it.price:.2f}", cell_style),
                Paragraph(f"{it.total_price:.2f}", cell_style),
            ]
            table_data.append(row)

    # Підсумок
    tot_row_idx = len(table_data)
    table_data.append([
        "", "", "", "", "",
        Paragraph("<b>ВСЬОГО:</b>", cell_style),
        Paragraph(f"<b>{total_qty}</b>", cell_style),
        "",
        Paragraph(f"<b>{total_amount:.2f}</b>", cell_style),
    ])

    col_widths = [75, 95, 90, 130, 65, 175, 40, 60, 70]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F497D")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
                ("BACKGROUND", (0, tot_row_idx), (-1, tot_row_idx), colors.HexColor("#D9E1F2")),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)
    return str(Path(output_path).resolve())


def export_counterparties_to_pdf(
    suppliers_data: List[Dict[str, Any]],
    customers_data: List[Dict[str, Any]],
    output_path: Path | str,
) -> str:
    """Генерація PDF-звіту: Обороти по контрагентах."""
    font_name = ensure_cyrillic_font()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=25,
        rightMargin=25,
        topMargin=25,
        bottomMargin=25,
    )
    elements = []

    title_style = ParagraphStyle(
        "TitleStyle",
        fontName=font_name,
        fontSize=14,
        leading=16,
        textColor=colors.HexColor("#1F497D"),
        alignment=1,
    )
    section_style = ParagraphStyle(
        "SectionStyle",
        fontName=font_name,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1F497D"),
        spaceBefore=10,
        spaceAfter=5,
    )
    cell_style = ParagraphStyle("CellStyle", fontName=font_name, fontSize=8, leading=10)
    header_style = ParagraphStyle("HeaderStyle", fontName=font_name, fontSize=8, leading=10, textColor=colors.white, alignment=1)

    elements.append(Paragraph("ЗВІТ: ОБОРОТИ ПО КОНТРАГЕНТАХ", title_style))
    elements.append(Spacer(1, 10))

    # 1. Постачальники
    elements.append(Paragraph("1. Поставки від постачальників:", section_style))
    h1 = ["№", "Постачальник", "Телефон", "Поставок", "Кількість", "Сума (грн)"]
    t1_data = [[Paragraph(h, header_style) for h in h1]]
    for idx, s in enumerate(suppliers_data, 1):
        t1_data.append([
            Paragraph(str(idx), cell_style),
            Paragraph(s.get("name", ""), cell_style),
            Paragraph(s.get("phone", "—") or "—", cell_style),
            Paragraph(str(s.get("doc_count", 0)), cell_style),
            Paragraph(str(s.get("total_quantity", 0)), cell_style),
            Paragraph(f"{s.get('total_amount', 0.0):.2f}", cell_style),
        ])
    t1 = Table(t1_data, colWidths=[25, 180, 95, 60, 65, 80])
    t1.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F497D")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ])
    )
    elements.append(t1)
    elements.append(Spacer(1, 15))

    # 2. Клієнти
    elements.append(Paragraph("2. Продажі клієнтам:", section_style))
    h2 = ["№", "Клієнт (покупець)", "Телефон", "Замовлень", "Кількість", "Сума (грн)"]
    t2_data = [[Paragraph(h, header_style) for h in h2]]
    for idx, c in enumerate(customers_data, 1):
        t2_data.append([
            Paragraph(str(idx), cell_style),
            Paragraph(c.get("name", ""), cell_style),
            Paragraph(c.get("phone", "—") or "—", cell_style),
            Paragraph(str(c.get("doc_count", 0)), cell_style),
            Paragraph(str(c.get("total_quantity", 0)), cell_style),
            Paragraph(f"{c.get('total_amount', 0.0):.2f}", cell_style),
        ])
    t2 = Table(t2_data, colWidths=[25, 180, 95, 60, 65, 80])
    t2.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F497D")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ])
    )
    elements.append(t2)

    doc.build(elements)
    return str(Path(output_path).resolve())


def export_invoice_to_pdf(document: Document, output_path: Path | str) -> str:
    """Друкована накладна у форматі PDF (офіційний бланк)."""
    font_name = ensure_cyrillic_font()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    elements = []

    title_text = "ПРИБУТКОВА НАКЛАДНА" if document.doc_type == "incoming" else "ВИДАТКОВА НАКЛАДНА"

    title_style = ParagraphStyle(
        "InvTitle",
        fontName=font_name,
        fontSize=15,
        leading=18,
        alignment=1,
    )
    sub_style = ParagraphStyle(
        "InvSub",
        fontName=font_name,
        fontSize=11,
        leading=14,
        alignment=1,
    )
    norm_style = ParagraphStyle("Norm", fontName=font_name, fontSize=9, leading=12)
    bold_style = ParagraphStyle("Bold", fontName=font_name, fontSize=9, leading=12)
    header_style = ParagraphStyle("Header", fontName=font_name, fontSize=8, leading=10, textColor=colors.white, alignment=1)

    elements.append(Paragraph(f"<b>{title_text} № {document.doc_number}</b>", title_style))
    elements.append(Paragraph(f"від {document.doc_date}", sub_style))
    elements.append(Spacer(1, 15))

    info_data = [
        [
            Paragraph("<b>Постачальник / Одержувач:</b>", bold_style),
            Paragraph(document.counterparty_name, norm_style),
        ],
        [
            Paragraph("<b>Відповідальна особа:</b>", bold_style),
            Paragraph(document.user_name or "—", norm_style),
        ],
        [
            Paragraph("<b>Примітки:</b>", bold_style),
            Paragraph(document.notes or "—", norm_style),
        ],
    ]
    info_table = Table(info_data, colWidths=[160, 360])
    info_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))

    headers = ["№", "Артикул", "Найменування товару", "Од.", "К-сть", "Ціна (грн)", "Сума (грн)"]
    table_data = [[Paragraph(h, header_style) for h in headers]]

    for idx, item in enumerate(document.items, 1):
        table_data.append([
            Paragraph(str(idx), norm_style),
            Paragraph(item.part_number or "—", norm_style),
            Paragraph(item.part_name or "—", norm_style),
            Paragraph(item.unit or "шт.", norm_style),
            Paragraph(str(item.quantity), norm_style),
            Paragraph(f"{item.price:.2f}", norm_style),
            Paragraph(f"{item.total_price:.2f}", norm_style),
        ])

    # Разом
    tot_row = len(table_data)
    table_data.append([
        "", "", Paragraph("<b>ВСЬОГО ДО СПЛАТИ:</b>", bold_style), "",
        Paragraph(f"<b>{document.total_quantity}</b>", bold_style),
        "",
        Paragraph(f"<b>{document.total_amount:.2f}</b>", bold_style),
    ])

    col_widths = [25, 75, 215, 35, 45, 60, 65]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F497D")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
            ("BACKGROUND", (0, tot_row), (-1, tot_row), colors.HexColor("#D9E1F2")),
            ("LINEABOVE", (0, tot_row), (-1, tot_row), 1, colors.black),
        ])
    )
    elements.append(table)
    elements.append(Spacer(1, 30))

    # Підписи сторін
    sign_data = [
        [
            Paragraph("<b>Відпустив:</b> ___________________", norm_style),
            Paragraph("<b>Отримав:</b> ___________________", norm_style),
        ]
    ]
    sign_table = Table(sign_data, colWidths=[260, 260])
    elements.append(sign_table)

    doc.build(elements)
    return str(Path(output_path).resolve())
