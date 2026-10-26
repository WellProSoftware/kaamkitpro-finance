from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill


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
    """Return a compact PDF summary using built-in PDF drawing commands."""
    # Avoid a large PDF dependency in the constrained Cloudflare Python Worker.
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

    # Standard PDF 1.4: one page, built-in Helvetica font, ASCII-safe content.
    def pdf_escape(value: str) -> str:
        value = value.encode("ascii", "replace").decode("ascii")
        return value.replace("\\\\", "\\\\\\\\").replace("(", "\\\\(").replace(")", "\\\\)")

    commands = ["BT", "/F1 7 Tf", "32 560 Td", "10 TL"]
    for index, line in enumerate(lines):
        if index:
            commands.append("T*")
        commands.append(f"({pdf_escape(line[:180])}) Tj")
    commands.append("ET")
    stream = "\\n".join(commands).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\\nstream\\n" + stream + b"\\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\\n%\\xe2\\xe3\\xcf\\xd3\\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\\n".encode("ascii") + obj + b"\\nendobj\\n")
    xref_offset = len(output)
    output.extend(f"xref\\n0 {len(offsets)}\\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \\n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \\n".encode("ascii"))
    output.extend(
        f"trailer\\n<< /Size {len(offsets)} /Root 1 0 R >>\\nstartxref\\n{xref_offset}\\n%%EOF".encode("ascii")
    )
    return bytes(output)
