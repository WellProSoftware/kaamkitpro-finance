from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_excel_report(projection: dict[str, Any]) -> bytes:
    """Return an editable XLSX workbook with formulas for key calculations."""
    wb = Workbook()
    assumptions = wb.active
    assumptions.title = "Assumptions"
    assumptions.append(["KaamKitPro Finance - Project Assumptions"])
    assumptions.append(["Project name", projection.get("project_name", "New Project")])
    assumptions.append(["Project type", projection.get("project_type", "Other")])
    assumptions.append(["Currency", projection.get("currency", "INR")])
    assumptions.append(["Project cost", projection.get("project_cost", 0)])
    assumptions.append(["Debt", projection.get("debt", 0)])
    assumptions.append(["Equity", projection.get("equity", 0)])
    assumptions.append([])
    assumptions.append(["Year", "Revenue", "Variable Cost", "Fixed Cost", "EBITDA", "Interest", "Principal", "Debt Service", "DSCR", "Cash After Debt Service"])

    for row in projection.get("annual_projection", []):
        r = assumptions.max_row + 1
        assumptions.append([
            row.get("year"),
            row.get("revenue", 0),
            row.get("variable_cost", 0),
            row.get("fixed_cost", 0),
            f"=B{r}-C{r}-D{r}",
            row.get("interest", 0),
            row.get("principal", 0),
            f"=F{r}+G{r}",
            f'=IF(H{r}=0,"",E{r}/H{r})',
            f"=E{r}-H{r}",
        ])

    for cell in assumptions[1]:
        cell.font = Font(bold=True, color="FFFFFF", size=14)
        cell.fill = PatternFill("solid", fgColor="173D93")
    for cell in assumptions[9]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2459D3")
        cell.alignment = Alignment(wrap_text=True)
    for column, width in {"A": 28, "B": 18, "C": 18, "D": 18, "E": 18, "F": 18, "G": 18, "H": 18, "I": 14, "J": 24}.items():
        assumptions.column_dimensions[column].width = width
    assumptions.freeze_panes = "A10"
    assumptions.sheet_view.showGridLines = False
    for row in assumptions.iter_rows(min_row=10, min_col=2, max_col=10):
        for cell in row:
            cell.number_format = '#,##0.00;[Red](#,##0.00);-'

    note = wb.create_sheet("Read Me")
    note.append(["Important limitations"])
    note.append(["This workbook is an early planning estimate, not an audited financial statement or bank-approved DPR."])
    note.append(["Review assumptions and formulas with a qualified finance professional before submitting to a lender."])
    note.column_dimensions["A"].width = 115
    note["A1"].font = Font(bold=True, color="FFFFFF")
    note["A1"].fill = PatternFill("solid", fgColor="173D93")
    note["A2"].alignment = Alignment(wrap_text=True)
    note["A3"].alignment = Alignment(wrap_text=True)

    output = BytesIO()
    wb.save(output)
    return output.getvalue()


def build_pdf_report(projection: dict[str, Any]) -> bytes:
    """Return a compact PDF summary of the projection."""
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("KaamKitPro Finance - Project Projection", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"Project: {projection.get('project_name', 'New Project')} | Type: {projection.get('project_type', 'Other')} | Currency: INR", styles["Normal"]),
        Spacer(1, 8),
        Paragraph(f"Project cost: ₹{projection.get('project_cost', 0):,.0f} | Debt: ₹{projection.get('debt', 0):,.0f} | Equity: ₹{projection.get('equity', 0):,.0f}", styles["Normal"]),
        Spacer(1, 14),
    ]
    data = [["Year", "Revenue", "Variable cost", "Fixed cost", "EBITDA", "Interest", "Principal", "DSCR", "Cash after debt"]]
    for row in projection.get("annual_projection", []):
        data.append([
            str(row.get("year", "")),
            f"{row.get('revenue', 0):,.0f}",
            f"{row.get('variable_cost', 0):,.0f}",
            f"{row.get('fixed_cost', 0):,.0f}",
            f"{row.get('ebitda', 0):,.0f}",
            f"{row.get('interest', 0):,.0f}",
            f"{row.get('principal', 0):,.0f}",
            "-" if row.get("dscr") is None else f"{row['dscr']:.2f}x",
            f"{row.get('cash_after_debt_service', 0):,.0f}",
        ])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173D93")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#DCE4EF")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7FB")]),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([table, Spacer(1, 12), Paragraph(
        "Disclaimer: Illustrative planning estimate only. Not an audited statement, loan approval, or bank-approved DPR. Validate assumptions, tax, working capital, depreciation and loan amortisation before external use.",
        styles["Italic"],
    )])
    doc.build(story)
    return output.getvalue()
