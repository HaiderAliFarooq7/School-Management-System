import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.school import School
from app.services.logo_store import logo_content


def _get_school(db: Session) -> School:
    school = db.execute(select(School).limit(1)).scalar_one_or_none()
    return school or School()


def generate_table_report_pdf(
    db: Session,
    dest,
    title: str,
    column_headers: list[str],
    rows: list[list[str]],
) -> None:
    """A generic landscape tabular report with the school name/logo as a
    header — used for the per-student pending-fee report and similar listings
    where the columns are chosen by the caller."""
    school = _get_school(db)
    margin = 10 * mm
    page_width, _ = landscape(A4)
    doc = SimpleDocTemplate(
        dest, pagesize=landscape(A4),
        topMargin=12 * mm, bottomMargin=12 * mm, leftMargin=margin, rightMargin=margin,
    )
    styles = getSampleStyleSheet()
    elements = []

    logo = logo_content(school)
    if logo:
        try:
            elements.append(Image(io.BytesIO(logo[0]), width=20 * mm, height=20 * mm))
        except Exception:
            pass

    elements.append(Paragraph(school.name or "School", styles["Title"]))
    elements.append(Paragraph(title, styles["Heading2"]))
    elements.append(Spacer(1, 6 * mm))

    table_data = [column_headers] + rows
    available_width = page_width - 2 * margin
    col_width = available_width / max(len(column_headers), 1)
    table = Table(table_data, repeatRows=1, colWidths=[col_width] * len(column_headers))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565c0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    doc.build(elements)
