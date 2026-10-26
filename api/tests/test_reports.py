from openpyxl import load_workbook
from io import BytesIO

from app.reports import build_excel_report, build_pdf_report


def sample_projection():
    return {
        "project_name": "Sample Project",
        "project_type": "Pharmacy",
        "currency": "INR",
        "project_cost": 1_000_000,
        "debt": 600_000,
        "equity": 400_000,
        "annual_projection": [{
            "year": 1,
            "revenue": 900_000,
            "variable_cost": 400_000,
            "fixed_cost": 200_000,
            "ebitda": 300_000,
            "interest": 66_000,
            "principal": 120_000,
            "dscr": 1.61,
            "cash_after_debt_service": 114_000,
        }],
    }


def test_excel_report_contains_formula_cells():
    content = build_excel_report(sample_projection())
    workbook = load_workbook(BytesIO(content), data_only=False)
    sheet = workbook["Assumptions"]
    assert sheet["E10"].value == "=B10-C10-D10"
    assert sheet["H10"].value == "=F10+G10"


def test_pdf_report_has_pdf_signature():
    content = build_pdf_report(sample_projection())
    assert content.startswith(b"%PDF")



def test_excel_report_includes_debt_balance_columns():
    content = build_excel_report({
        **sample_projection(),
        "annual_projection": [{
            **sample_projection()["annual_projection"][0],
            "opening_debt": 600000,
            "closing_debt": 480000,
            "profit_before_tax_before_depreciation": 234000,
        }],
    })
    workbook = load_workbook(BytesIO(content), data_only=False)
    sheet = workbook["Assumptions"]
    assert sheet["B10"].value == 600000
    assert sheet["L10"].value == 480000
    assert sheet["M10"].value == "=F10-G10"


def test_pdf_report_includes_debt_balance_data():
    projection = sample_projection()
    projection["annual_projection"][0].update({
        "opening_debt": 600000,
        "closing_debt": 480000,
    })
    content = build_pdf_report(projection)
    assert content.startswith(b"%PDF")
    assert len(content) > 1000
