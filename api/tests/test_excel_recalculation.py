"""Integration test for real Excel formula calculation via LibreOffice Calc."""
from __future__ import annotations

import shutil
import subprocess
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import load_workbook

from app.reports import build_excel_report


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

    # Keep the generated workbook formulas intact, then let Calc calculate and
    # persist cached formula results for openpyxl's data_only reader.
    profile = (tmp_path / "lo-profile").as_uri()
    result = subprocess.run(
        [
            "soffice",
            "--headless",
            f"-env:UserInstallation={profile}",
            "--convert-to",
            "xlsx",
            "--outdir",
            str(tmp_path / "recalculated"),
            str(source),
        ],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    calculated_path = tmp_path / "recalculated" / source.name
    assert calculated_path.exists(), result.stdout + result.stderr
    workbook = load_workbook(calculated_path, data_only=True)
    assumptions = workbook["Assumptions"]
    summary = workbook["Executive Summary"]

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

    # No spreadsheet formula errors in key output ranges.
    for sheet_name, cell_range in (
        ("Assumptions", ("A10", "M12")),
        ("Executive Summary", ("A8", "F10")),
    ):
        sheet = workbook[sheet_name]
        start, end = cell_range
        for row in sheet[start:end]:
            for cell in row:
                assert not (
                    isinstance(cell.value, str)
                    and cell.value.startswith("#")
                ), f"Formula error at {sheet_name}!{cell.coordinate}: {cell.value}"
