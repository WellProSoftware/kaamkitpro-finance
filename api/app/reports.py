from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_excel_report(projection: dict[str, Any]) -> bytes:
    """Return an editable XLSX workbook with annual projections and debt schedule."""
    wb = Workbook()
    sheet = wb.active
    sheet.title = "Assumptions"
    sheet.append(["KaamKitPro Finance - Project Assumptions"])
    sheet.append(["Project name", projection.get("project_name", "New Project")])
    sheet.append(["Project type", projection.get("project_type", "Other")])
    sheet.append(["Currency", projection.get("currency", "INR")])
    sheet.append(["Project cost", projection.get("project_cost", 0)])
    sheet.append(["Debt", projection.get("debt", 0)])
    sheet.append(["Equity", projection.get("equity", 0)])
    sheet.append([])
    sheet.append([
        "Year", "Opening Debt", "Revenue", "Variable Cost", "Fixed Cost",
        "EBITDA", "Interest", "Principal", "Debt Service", "DSCR",
        "Cash After Debt Service", "Closing Debt", "Profit Before Tax (Pre-Depreciation)",
    ])

    for row in projection.get("annual_projection", []):
        r = sheet.max_row + 1
        sheet.append([
            row.get("year"),
            row.get("opening_debt", 0),
            row.get("revenue", 0),
            row.get("variable_cost", 0),
            row.get("fixed_cost", 0),
            f"=C{r}-D{r}-E{r}",
            row.get("interest", 0),
            row.get("principal", 0),
            f"=G{r}+H{r}",
            f'=IF(I{r}=0,"",F{r}/I{r})',
            f"=F{r}-I{r}",
            row.get("closing_debt", 0),
            f"=F{r}-G{r}",
        ])

    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF", size=14)
        cell.fill = PatternFill("solid", fgColor="173D93")
    for cell in sheet[9]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2459D3")
        cell.alignment = Alignment(wrap_text=True)
    widths = {"A": 28, "B": 18, "C": 18, "D": 18, "E": 18, "F": 18,
              "G": 18, "H": 18, "I": 18, "J": 14, "K": 24, "L": 18, "M": 32}
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    sheet.freeze_panes = "A10"
    sheet.sheet_view.showGridLines = False
    for row in sheet.iter_rows(min_row=10, min_col=2, max_col=13):
        for cell in row:
            cell.number_format = '#,##0.00;[Red](#,##0.00);-'

    note = wb.create_sheet("Read Me")
    note.append(["Important limitations"])
    note.append(["This workbook is an early planning estimate, not an audited financial statement or bank-approved DPR."])
    note.append(["Loan schedule uses equal annual principal repayments with interest calculated on opening balance; it is not an EMI schedule."])
    note.append(["Profit before tax shown here is before depreciation and tax; it is not net profit."])
    note.append(["Review assumptions and formulas with a qualified finance professional before submitting to a lender."])
    note.column_dimensions["A"].width = 115
    note["A1"].font = Font(bold=True, color="FFFFFF")
    note["A1"].fill = PatternFill("solid", fgColor="173D93")
    for cell in ("A2", "A3", "A4", "A5"):
        note[cell].alignment = Alignment(wrap_text=True)

    output = BytesIO()
    wb.save(output)
    return output.getvalue()


def build_pdf_report(projection: dict[str, Any]) -> bytes:
    """Return a compact PDF summary with annual debt balances."""
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=22, leftMargin=22, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("KaamKitPro Finance - Project Projection", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"Project: {projection.get('project_name', 'New Project')} | Type: {projection.get('project_type', 'Other')} | Currency: INR", styles["Normal"]),
        Spacer(1, 8),
        Paragraph(f"Project cost: ₹{projection.get('project_cost', 0):,.0f} | Debt: ₹{projection.get('debt', 0):,.0f} | Equity: ₹{projection.get('equity', 0):,.0f}", styles["Normal"]),
        Spacer(1, 14),
    ]
    data = [["Year", "Opening debt", "Revenue", "Variable cost", "Fixed cost", "EBITDA", "Interest", "Principal", "Closing debt", "DSCR", "Cash after debt"]]
    for row in projection.get("annual_projection", []):
        data.append([
            str(row.get("year", "")),
            f"{row.get('opening_debt', 0):,.0f}",
            f"{row.get('revenue', 0):,.0f}",
            f"{row.get('variable_cost', 0):,.0f}",
            f"{row.get('fixed_cost', 0):,.0f}",
            f"{row.get('ebitda', 0):,.0f}",
            f"{row.get('interest', 0):,.0f}",
            f"{row.get('principal', 0):,.0f}",
            f"{row.get('closing_debt', 0):,.0f}",
            "-" if row.get("dscr") is None else f"{row['dscr']:.2f}x",
            f"{row.get('cash_after_debt_service', 0):,.0f}",
        ])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#173D93")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#DCE4EF")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7FB")]),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Spacer(1, 12), Paragraph(
        "Disclaimer: Illustrative planning estimate only. Loan repayment uses equal annual principal, not EMI; interest is calculated on opening balance. Profit before tax indicator is before depreciation and tax, not net profit. This is not an audited statement, loan approval, or bank-approved DPR. Validate assumptions, tax, working capital, depreciation and loan amortisation before external use.",
        styles["Italic"],
    )])
    doc.build(story)
    return output.getvalue()
