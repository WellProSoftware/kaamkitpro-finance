"""Integration test for real Excel formula calculation via LibreOffice Calc."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from openpyxl import load_workbook

from app.reports import build_excel_report


def recalculate_with_libreoffice(source: Path, output_dir: Path, profile: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "soffice",
            "--headless",
            f"-env:UserInstallation={profile.as_uri()}",
            "--convert-to",
            "xlsx",
            "--outdir",
            str(output_dir),
            str(source),
        ],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    calculated_path = output_dir / source.name
    assert calculated_path.exists(), result.stdout + result.stderr
    return calculated_path


def assert_no_formula_errors(workbook) -> None:
    for sheet_name, cell_range in (
        # Scan the complete supported forecast area, not only the first few years.
        ("Assumptions", ("A10", "M109")),
        ("Executive Summary", ("A8", "F107")),
    ):
        sheet = workbook[sheet_name]
        start, end = cell_range
        for row in sheet[start:end]:
            for cell in row:
                assert not (
                    isinstance(cell.value, str)
                    and cell.value.startswith("#")
                ), f"Formula error at {sheet_name}!{cell.coordinate}: {cell.value}"


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice is not installed")
def test_excel_workbook_recalculates_live_forecast_and_summary(tmp_path: Path) -> None:
    projection = {
        "project_name": "Calc integration test",
        "project_type": "Other",
        "currency": "INR",
        "project_cost": 1_000_000,
        "debt": 600_000,
        "equity": 400_000,
        "model_inputs": {
            "debt_pct": 60,
            "monthly_revenue": 100_000,
            "growth_pct": 10,
            "variable_cost_pct": 40,
            "monthly_fixed_cost": 20_000,
            "interest_pct": 10,
            "loan_years": 5,
            "projection_years": 3,
        },
        "annual_projection": [],
    }

    source = tmp_path / "finance-model.xlsx"
    source.write_bytes(build_excel_report(projection))

    # First pass: calculate the workbook with its original assumptions.
    baseline_path = recalculate_with_libreoffice(
        source, tmp_path / "baseline", tmp_path / "lo-profile-baseline"
    )
    baseline = load_workbook(baseline_path, data_only=True)
    assumptions = baseline["Assumptions"]
    summary = baseline["Executive Summary"]

    # Revenue is 12 * monthly revenue, growing by 10% per year.
    assert assumptions["C10"].value == pytest.approx(1_200_000)
    assert assumptions["C11"].value == pytest.approx(1_320_000)
    assert assumptions["C12"].value == pytest.approx(1_452_000)

    # Debt schedule, debt-service coverage and summary references recalculate.
    assert assumptions["B10"].value == pytest.approx(600_000)
    assert assumptions["H10"].value == pytest.approx(120_000)
    assert assumptions["G10"].value == pytest.approx(60_000)
    expected_dscr = (1_200_000 - 480_000 - 240_000) / (60_000 + 120_000)
    assert assumptions["J10"].value == pytest.approx(expected_dscr)
    assert assumptions["L10"].value == pytest.approx(480_000)
    assert summary["B8"].value == pytest.approx(1_200_000)
    assert summary["C8"].value == pytest.approx(480_000)
    assert_no_formula_errors(baseline)

    # Change a yellow editable input and recalculate a second copy. The
    # formula outputs must follow the input rather than retain stale values.
    edited_source = tmp_path / "finance-model-edited.xlsx"
    editable = load_workbook(source, data_only=False)
    editable["Model Inputs"]["B7"] = 120_000
    editable.save(edited_source)

    edited_path = recalculate_with_libreoffice(
        edited_source, tmp_path / "edited", tmp_path / "lo-profile-edited"
    )
    edited = load_workbook(edited_path, data_only=True)
    edited_assumptions = edited["Assumptions"]
    edited_summary = edited["Executive Summary"]

    assert edited_assumptions["C10"].value == pytest.approx(1_440_000)
    assert edited_assumptions["C11"].value == pytest.approx(1_584_000)
    assert edited_assumptions["F10"].value == pytest.approx(624_000)
    assert edited_summary["B8"].value == pytest.approx(1_440_000)
    assert edited_summary["C8"].value == pytest.approx(624_000)
    assert edited_assumptions["C10"].value != assumptions["C10"].value
    assert_no_formula_errors(edited)


def test_excel_model_inputs_have_validation_for_all_numeric_assumptions() -> None:
    """Guard against accidentally removing spreadsheet input safeguards."""
    workbook_bytes = build_excel_report(
        {
            "project_name": "Validation test",
            "project_type": "Other",
            "currency": "INR",
            "project_cost": 1_000_000,
            "debt": 600_000,
            "annual_projection": [],
            "model_inputs": {
                "debt_pct": 60,
                "monthly_revenue": 100_000,
                "growth_pct": 10,
                "variable_cost_pct": 40,
                "monthly_fixed_cost": 20_000,
                "interest_pct": 10,
                "loan_years": 5,
                "projection_years": 3,
            },
        }
    )
    import io

    workbook = load_workbook(io.BytesIO(workbook_bytes), data_only=False)
    inputs = workbook["Model Inputs"]
    validated_coordinates = {
        coordinate
        for validation in inputs.data_validations.dataValidation
        for coordinate in str(validation.sqref).split()
    }

    # Numeric inputs B5:B13 must have explicit validation rules, including
    # project cost, debt %, monthly revenue, growth, costs, interest and terms.
    assert {f"B{row}" for row in range(5, 14)} <= validated_coordinates

    validation_by_cell = {
        coordinate: validation
        for validation in inputs.data_validations.dataValidation
        for coordinate in str(validation.sqref).split()
    }
    assert validation_by_cell["B6"].type == "decimal"
    assert validation_by_cell["B6"].operator == "between"
    assert validation_by_cell["B12"].type == "whole"
    assert validation_by_cell["B13"].type == "whole"


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice is not installed")
@pytest.mark.parametrize(
    ("project_cost", "debt_pct"),
    [(0, 50), (1_000_000, 0)],
    ids=("zero-project-cost", "zero-debt"),
)
def test_excel_workbook_handles_zero_cost_or_zero_debt(
    tmp_path: Path, project_cost: float, debt_pct: float
) -> None:
    """Zero-cost and zero-debt scenarios should not produce formula errors."""
    projection = {
        "project_name": "Zero-value edge case",
        "project_type": "Other",
        "currency": "INR",
        "project_cost": project_cost,
        "debt": project_cost * debt_pct / 100,
        "equity": project_cost * (1 - debt_pct / 100),
        "model_inputs": {
            "debt_pct": debt_pct,
            "monthly_revenue": 0,
            "growth_pct": 0,
            "variable_cost_pct": 40,
            "monthly_fixed_cost": 0,
            "interest_pct": 10,
            "loan_years": 5,
            "projection_years": 1,
        },
        "annual_projection": [],
    }
    source = tmp_path / "zero-case.xlsx"
    source.write_bytes(build_excel_report(projection))
    calculated_path = recalculate_with_libreoffice(
        source, tmp_path / "calculated", tmp_path / "lo-profile"
    )
    workbook = load_workbook(calculated_path, data_only=True)
    assumptions = workbook["Assumptions"]
    summary = workbook["Executive Summary"]

    assert assumptions["B10"].value == pytest.approx(project_cost * debt_pct / 100)
    assert assumptions["C10"].value == pytest.approx(0)
    assert assumptions["G10"].value == pytest.approx(0)
    assert assumptions["H10"].value == pytest.approx(0)
    assert assumptions["I10"].value == pytest.approx(0)
    assert assumptions["J10"].value in (None, "")
    assert summary["D5"].value in (None, "")
    assert_no_formula_errors(workbook)
