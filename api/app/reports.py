from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins


NAVY = "173D93"
BLUE = "2459D3"
PALE_BLUE = "EAF1FF"
WHITE = "FFFFFF"
GREY = "5B6573"
LIGHT_GREY = "F3F5F8"
GREEN = "E2F0D9"
THIN_GREY = Side(style="thin", color="D9E0EA")


def build_excel_report(projection: dict[str, Any]) -> bytes:
    """Return a formatted, editable XLSX workbook with summary and annual projections."""
    wb = Workbook()
    summary = wb.active
    summary.title = "Executive Summary"
    assumptions = wb.create_sheet("Assumptions")
    notes = wb.create_sheet("Read Me")

    project_name = projection.get("project_name", "New Project")
    project_type = projection.get("project_type", "Other")
    currency = projection.get("currency", "INR")
    project_cost = projection.get("project_cost", 0) or 0
    debt = projection.get("debt", 0) or 0
    equity = projection.get("equity", 0) or 0
    annual = projection.get("annual_projection", [])

    # Executive summary
    summary.append(["KAAMKITPRO FINANCE | PROJECT SUMMARY"])
    summary.append(["Project", project_name, "Project Type", project_type])
    summary.append(["Currency", currency, "Projection Period (Years)", len(annual)])
    summary.append(["Project Cost", project_cost, "Debt Funding", debt])
    summary.append(["Equity Funding", equity, "Debt / Equity", (debt / equity if equity else None)])
    summary.append([])
    summary.append(["YEAR", "REVENUE", "EBITDA", "DEBT SERVICE", "DSCR", "CASH AFTER DEBT"])
    for row in annual:
        summary.append([
            row.get("year"),
            row.get("revenue", 0),
            row.get("ebitda", 0),
            (row.get("interest", 0) or 0) + (row.get("principal", 0) or 0),
            row.get("dscr"),
            row.get("cash_after_debt_service", 0),
        ])
    summary.append([])
    summary.append(["Planning note", "Illustrative estimate only; validate assumptions before using for lending or investment decisions."])

    # Detailed assumptions and annual projection
    assumptions.append(["KAAMKITPRO FINANCE | PROJECT ASSUMPTIONS & PROJECTION"])
    assumptions.append(["Project name", project_name])
    assumptions.append(["Project type", project_type])
    assumptions.append(["Currency", currency])
    assumptions.append(["Project cost", project_cost])
    assumptions.append(["Debt", debt])
    assumptions.append(["Equity", equity])
    assumptions.append([])
    headers = [
        "Year", "Opening Debt", "Revenue", "Variable Cost", "Fixed Cost", "EBITDA",
        "Interest", "Principal", "Debt Service", "DSCR", "Cash After Debt Service",
        "Closing Debt", "Profit Before Tax (Pre-Depreciation)",
    ]
    assumptions.append(headers)
    for row in annual:
        r = assumptions.max_row + 1
        assumptions.append([
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

    # Consistent workbook styling
    for ws in (summary, assumptions, notes):
        ws.sheet_view.showGridLines = False
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.page_setup.orientation = "landscape"
        ws.page_margins = PageMargins(left=0.25, right=0.25, top=0.5, bottom=0.5, header=0.2, footer=0.2)
        ws.oddFooter.center.text = "KaamKitPro Finance | Illustrative planning estimate"
        ws.oddFooter.right.text = "Page &P of &N"

    for ws, title_row in ((summary, 1), (assumptions, 1), (notes, 1)):
        ws.merge_cells(start_row=title_row, start_column=1, end_row=title_row, end_column=(6 if ws is summary else 13 if ws is assumptions else 1))
        cell = ws.cell(title_row, 1)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(bold=True, color=WHITE, size=16)
        cell.alignment = Alignment(vertical="center")
        ws.row_dimensions[title_row].height = 30

    for cell in summary[7]:
        cell.fill = PatternFill("solid", fgColor=BLUE)
        cell.font = Font(bold=True, color=WHITE)
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    summary.row_dimensions[7].height = 32
    for r in range(2, 6):
        for c in (1, 3):
            summary.cell(r, c).font = Font(bold=True, color=GREY)
        for c in (2, 4):
            summary.cell(r, c).fill = PatternFill("solid", fgColor=PALE_BLUE)
    for r in range(8, 8 + len(annual)):
        if r % 2 == 0:
            for c in range(1, 7):
                summary.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT_GREY)
    summary.column_dimensions["A"].width = 25
    for col in "BCDEF":
        summary.column_dimensions[col].width = 22
    summary.freeze_panes = "A8"
    summary.auto_filter.ref = f"A7:F{max(7, 7 + len(annual))}"

    for cell in assumptions[9]:
        cell.fill = PatternFill("solid", fgColor=BLUE)
        cell.font = Font(bold=True, color=WHITE)
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    assumptions.row_dimensions[9].height = 34
    widths = [10, 18, 18, 18, 18, 18, 16, 16, 18, 12, 24, 18, 32]
    for i, width in enumerate(widths, start=1):
        assumptions.column_dimensions[get_column_letter(i)].width = width
    assumptions.freeze_panes = "A10"
    assumptions.auto_filter.ref = f"A9:M{max(9, 9 + len(annual))}"

    money_format = '#,##0.00;[Red](#,##0.00);-'
    for ws, first_data_row, last_data_row, cols in (
        (summary, 8, 7 + len(annual), (2, 3, 4, 6)),
        (assumptions, 10, 9 + len(annual), tuple(range(2, 10)) + (11, 12, 13)),
    ):
        for r in range(first_data_row, last_data_row + 1):
            for c in cols:
                ws.cell(r, c).number_format = f'"{currency} " {money_format}'
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c).border = Border(bottom=THIN_GREY)
                ws.cell(r, c).alignment = Alignment(vertical="center")
    for r in range(8, 8 + len(annual)):
        summary.cell(r, 5).number_format = '0.00"x"'
    for r in range(10, 10 + len(annual)):
        assumptions.cell(r, 10).number_format = '0.00"x"'
    for cell_ref in ("B5", "D5"):
        summary[cell_ref].number_format = "0.00x" if cell_ref == "D5" else f'"{currency} " {money_format}'
    for cell_ref in ("B5", "B6", "B7"):
        assumptions[cell_ref].number_format = f'"{currency} " {money_format}'

    # Revenue and EBITDA comparison chart
    if annual:
        chart = BarChart()
        chart.type = "col"
        chart.style = 10
        chart.title = "Revenue vs EBITDA"
        chart.y_axis.title = currency
        chart.x_axis.title = "Year"
        chart.height = 7
        chart.width = 14
        chart.add_data(Reference(summary, min_col=2, max_col=3, min_row=7, max_row=7 + len(annual)), titles_from_data=True)
        chart.set_categories(Reference(summary, min_col=1, min_row=8, max_row=7 + len(annual)))
        summary.add_chart(chart, "A16")

    # Read Me / limitations
    notes.append(["Important limitations"])
    notes.append(["This workbook is an illustrative planning estimate, not an audited financial statement or bank-approved DPR."])
    notes.append(["The debt schedule uses equal annual principal repayments with interest calculated on opening balance; it is not an EMI schedule."])
    notes.append(["Profit before tax shown is before depreciation and tax; it is not net profit."])
    notes.append(["Annual projection values are generated by the API. Some spreadsheet formulas recalculate derived values, but changing assumptions does not yet rebuild the full projection model."])
    notes.append(["Review assumptions and formulas with a qualified finance professional before submitting to a lender or investor."])
    notes.column_dimensions["A"].width = 115
    notes.row_dimensions[1].height = 28
    for cell in notes[1]:
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(bold=True, color=WHITE, size=14)
    for r in range(2, notes.max_row + 1):
        notes.cell(r, 1).alignment = Alignment(wrap_text=True, vertical="top")
        notes.row_dimensions[r].height = 36

    output = BytesIO()
    wb.save(output)
    return output.getvalue()


def build_pdf_report(projection: dict[str, Any]) -> bytes:
    """Return a compact, valid PDF summary using built-in PDF drawing commands."""
    lines = [
        "KaamKitPro Finance - Project Projection",
        f"Project: {projection.get('project_name', 'New Project')} | Type: {projection.get('project_type', 'Other')} | Currency: {projection.get('currency', 'INR')}",
        f"Project cost: INR {projection.get('project_cost', 0):,.0f} | Debt: INR {projection.get('debt', 0):,.0f} | Equity: INR {projection.get('equity', 0):,.0f}",
        "",
        "Year | Opening debt | Revenue | Variable cost | Fixed cost | EBITDA | Interest | Principal | Closing debt | DSCR | Cash after debt",
    ]
    for row in projection.get("annual_projection", []):
        dscr = "-" if row.get("dscr") is None else f"{row['dscr']:.2f}x"
        lines.append(
            f"{row.get('year', '')} | {row.get('opening_debt', 0):,.0f} | "
            f"{row.get('revenue', 0):,.0f} | {row.get('variable_cost', 0):,.0f} | "
            f"{row.get('fixed_cost', 0):,.0f} | {row.get('ebitda', 0):,.0f} | "
            f"{row.get('interest', 0):,.0f} | {row.get('principal', 0):,.0f} | "
            f"{row.get('closing_debt', 0):,.0f} | {dscr} | "
            f"{row.get('cash_after_debt_service', 0):,.0f}"
        )
    lines.extend([
        "",
        "Disclaimer: Illustrative planning estimate only. Equal annual principal repayment is used, not EMI.",
        "Interest is calculated on opening balance. Profit before tax is before depreciation and tax.",
        "This is not an audited statement, loan approval, or bank-approved DPR. Validate assumptions before use.",
    ])

    def pdf_escape(value: str) -> str:
        value = value.encode("ascii", "replace").decode("ascii")
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    commands = ["BT", "/F1 7 Tf", "32 560 Td", "10 TL"]
    for index, line in enumerate(lines):
        if index:
            commands.append("T*")
        commands.append(f"({pdf_escape(line[:180])}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)
