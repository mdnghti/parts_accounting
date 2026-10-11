from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from db.connection import get_connection
from db.repositories import get_documents, get_parts
from models.document import Document
from models.part import Part
from reports.excel_generator import (
    export_counterparties_to_excel,
    export_invoice_to_excel,
    export_movement_to_excel,
    export_stock_to_excel,
)
from reports.pdf_generator import (
    export_counterparties_to_pdf,
    export_invoice_to_pdf,
    export_movement_to_pdf,
    export_stock_to_pdf,
)


def get_stock_report_data() -> List[Part]:
    """Отримання списку всіх запчастин для звіту по залишках."""
    return get_parts()


def get_movement_report_data(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Document]:
    """Отримання документів з позиціями за період."""
    from db.repositories import get_document_by_id

    summaries = get_documents(date_from=date_from, date_to=date_to)
    full_docs = []
    for s in summaries:
        doc = get_document_by_id(s.id)
        if doc:
            full_docs.append(doc)
    return full_docs


def get_counterparties_report_data() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Агрегація оборотів по постачальниках та клієнтах."""
    conn = get_connection()
    try:
        cur = conn.cursor()

        # 1. Постачальники (прибуткові накладні)
        cur.execute(
            """
            SELECT s.id, s.name, s.phone,
                   COUNT(DISTINCT d.id) AS doc_count,
                   COALESCE(SUM(di.quantity), 0) AS total_quantity,
                   COALESCE(SUM(di.quantity * di.price), 0.0) AS total_amount
            FROM suppliers s
            LEFT JOIN documents d ON s.id = d.counterparty_id AND d.doc_type = 'incoming'
            LEFT JOIN document_items di ON d.id = di.document_id
            GROUP BY s.id, s.name, s.phone
            ORDER BY total_amount DESC, s.name ASC
            """
        )
        suppliers_data = [dict(r) for r in cur.fetchall()]

        # 2. Клієнти (видаткові накладні)
        cur.execute(
            """
            SELECT c.id, c.name, c.phone,
                   COUNT(DISTINCT d.id) AS doc_count,
                   COALESCE(SUM(di.quantity), 0) AS total_quantity,
                   COALESCE(SUM(di.quantity * di.price), 0.0) AS total_amount
            FROM customers c
            LEFT JOIN documents d ON c.id = d.counterparty_id AND d.doc_type = 'outgoing'
            LEFT JOIN document_items di ON d.id = di.document_id
            GROUP BY c.id, c.name, c.phone
            ORDER BY total_amount DESC, c.name ASC
            """
        )
        customers_data = [dict(r) for r in cur.fetchall()]

        return suppliers_data, customers_data
    finally:
        conn.close()


def generate_report(
    report_type: str,  # 'stock', 'movement', 'counterparties', 'invoice'
    export_format: str,  # 'excel' або 'pdf'
    output_path: Path | str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    document: Optional[Document] = None,
) -> str:
    """Універсальний диспетчер створення звітів."""
    if report_type == "stock":
        parts = get_stock_report_data()
        if export_format == "excel":
            return export_stock_to_excel(parts, output_path)
        else:
            return export_stock_to_pdf(parts, output_path)

    elif report_type == "movement":
        docs = get_movement_report_data(date_from=date_from, date_to=date_to)
        if export_format == "excel":
            return export_movement_to_excel(docs, output_path)
        else:
            return export_movement_to_pdf(docs, output_path)

    elif report_type == "counterparties":
        sups, custs = get_counterparties_report_data()
        if export_format == "excel":
            return export_counterparties_to_excel(sups, custs, output_path)
        else:
            return export_counterparties_to_pdf(sups, custs, output_path)

    elif report_type == "invoice":
        if not document:
            raise ValueError("Для формування накладної обов'язково передати об'єкт Document.")
        if export_format == "excel":
            return export_invoice_to_excel(document, output_path)
        else:
            return export_invoice_to_pdf(document, output_path)

    else:
        raise ValueError(f"Невідомий тип звіту: {report_type}")
