from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def payload():
    return {
        "project_name": "Test Pharmacy",
        "project_type": "Pharmacy",
        "project_cost": 1_000_000,
        "debt_pct": 60,
        "monthly_revenue": 150_000,
        "growth_pct": 5,
        "variable_cost_pct": 55,
        "monthly_fixed_cost": 25_000,
        "interest_pct": 11,
        "loan_years": 5,
        "projection_years": 3,
    }


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_lists_docs_and_endpoints():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"
    assert "/api/reports/excel" in response.json()["endpoints"]


def test_projection_endpoint_returns_requested_years():
    response = client.post("/api/projection", json=payload())
    assert response.status_code == 200
    body = response.json()
    assert body["project_name"] == "Test Pharmacy"
    assert len(body["annual_projection"]) == 3
    assert body["debt"] + body["equity"] == body["project_cost"]


def test_excel_endpoint_returns_xlsx():
    response = client.post("/api/reports/excel", json=payload())
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]
    assert response.content.startswith(b"PK")


def test_pdf_endpoint_returns_pdf():
    response = client.post("/api/reports/pdf", json=payload())
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_rejects_invalid_debt_percentage():
    response = client.post("/api/projection", json={**payload(), "debt_pct": 150})
    assert response.status_code == 422


def test_rejects_negative_project_cost():
    response = client.post("/api/projection", json={**payload(), "project_cost": -1})
    assert response.status_code == 422


def test_rejects_unreasonably_large_project_cost():
    response = client.post(
        "/api/projection",
        json={**payload(), "project_cost": 1e16},
    )
    assert response.status_code == 422


def test_excel_endpoint_rejects_invalid_assumptions():
    response = client.post(
        "/api/reports/excel",
        json={**payload(), "variable_cost_pct": 101},
    )
    assert response.status_code == 422


def test_pdf_endpoint_rejects_invalid_assumptions():
    response = client.post(
        "/api/reports/pdf",
        json={**payload(), "loan_years": 0},
    )
    assert response.status_code == 422


def test_projection_accepts_more_than_ten_years():
    response = client.post(
        "/api/projection",
        json={**payload(), "projection_years": 25},
    )
    assert response.status_code == 200
    assert len(response.json()["annual_projection"]) == 25


def test_projection_rejects_more_than_one_hundred_years():
    response = client.post(
        "/api/projection",
        json={**payload(), "projection_years": 101},
    )
    assert response.status_code == 422


def test_cors_allows_local_frontend_origin():
    response = client.options(
        "/api/projection",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_does_not_allow_unconfigured_origin():
    response = client.options(
        "/api/projection",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_projection_includes_reconciled_loan_schedule():
    response = client.post("/api/projection", json=payload())
    assert response.status_code == 200
    body = response.json()
    assert len(body["debt_schedule"]) == 3
    for row in body["debt_schedule"]:
        assert round(row["opening_balance"] - row["principal_repayment"], 2) == row["closing_balance"]
        assert round(row["interest_payment"] + row["principal_repayment"], 2) == row["total_debt_service"]


def test_report_endpoints_include_download_filenames():
    excel = client.post("/api/reports/excel", json=payload())
    pdf = client.post("/api/reports/pdf", json=payload())
    assert "filename=\"kaamkitpro-finance-projection.xlsx\"" in excel.headers["content-disposition"]
    assert "filename=\"kaamkitpro-finance-projection.pdf\"" in pdf.headers["content-disposition"]


def test_pdf_and_excel_endpoints_use_the_same_submitted_funding_assumptions():
    from io import BytesIO

    from openpyxl import load_workbook

    request = {**payload(), "project_cost": 3_500_000, "debt_pct": 60}
    excel_response = client.post("/api/reports/excel", json=request)
    pdf_response = client.post("/api/reports/pdf", json=request)

    assert excel_response.status_code == 200
    assert pdf_response.status_code == 200
    workbook = load_workbook(BytesIO(excel_response.content), data_only=False)
    inputs = workbook["Model Inputs"]
    pdf = pdf_response.content

    assert inputs["B15"].value == request["project_cost"]
    assert inputs["B6"].value == request["debt_pct"]
    assert f"Project cost: INR {request['project_cost']:,.0f}".encode() in pdf
    assert f"Debt: INR {request['project_cost'] * request['debt_pct'] / 100:,.0f}".encode() in pdf
    assert f"Equity: INR {request['project_cost'] * (1 - request['debt_pct'] / 100):,.0f}".encode() in pdf


def test_itemized_costs_drive_projection_and_both_reports():
    from io import BytesIO

    from openpyxl import load_workbook

    itemized = {
        "Outsourcing": 1_500_000,
        "Warehouse setup": 2_000_000,
        "Hospital setup / expansion": 500_000,
        "Retail / pharmacy setup or expansion": 0,
        "Optical setup or expansion": 0,
        "Equipment and technology": 0,
        "Licences, deposits and professional fees": 0,
        "Initial inventory and working capital": 0,
        "Other project costs": 0,
    }
    request = {**payload(), "project_cost": 1_000_000, "debt_pct": 60, "itemized_costs": itemized}
    projection = client.post("/api/projection", json=request)
    excel = client.post("/api/reports/excel", json=request)
    pdf = client.post("/api/reports/pdf", json=request)

    assert projection.status_code == 200
    assert projection.json()["project_cost"] == 4_000_000
    assert projection.json()["debt"] == 2_400_000
    assert projection.json()["equity"] == 1_600_000
    assert excel.status_code == 200 and pdf.status_code == 200

    workbook = load_workbook(BytesIO(excel.content), data_only=False)
    inputs = workbook["Model Inputs"]
    costs = workbook["Project Cost Breakdown"]
    assert inputs["B14"].value == "Itemized costs"
    assert inputs["B5"].value == '=IF(B14="Itemized costs",B16,B15)'
    assert costs["B3"].value == 1_500_000
    assert costs["B4"].value == 2_000_000
    assert costs["B5"].value == 500_000
    assert costs["B12"].value == "=SUM(B3:B11)"
    assert b"Project cost: INR 4,000,000" in pdf.content
    assert b"Debt: INR 2,400,000" in pdf.content
    assert b"Equity: INR 1,600,000" in pdf.content


def test_itemized_costs_reject_unknown_categories_and_negative_amounts():
    unknown = client.post(
        "/api/projection",
        json={**payload(), "itemized_costs": {"Mystery cost": 100}},
    )
    negative = client.post(
        "/api/projection",
        json={**payload(), "itemized_costs": {"Outsourcing": -1}},
    )
    oversized_total = client.post(
        "/api/projection",
        json={**payload(), "itemized_costs": {"Outsourcing": 1_000_000_000_000_001}},
    )
    assert unknown.status_code == 422
    assert negative.status_code == 422
    assert oversized_total.status_code == 422

def test_projection_handles_zero_debt_without_division_errors():
    response = client.post(
        "/api/projection",
        json={**payload(), "project_cost": 0, "debt_pct": 0},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["debt"] == 0
    assert body["equity"] == 0
    assert all(row["debt_service"] == 0 for row in body["annual_projection"])
    assert all(row["dscr"] is None for row in body["annual_projection"])


def test_projection_handles_one_hundred_percent_variable_cost():
    response = client.post(
        "/api/projection",
        json={**payload(), "variable_cost_pct": 100},
    )
    assert response.status_code == 200
    body = response.json()
    assert all(row["break_even_revenue"] is None for row in body["annual_projection"])
    assert all(row["variable_cost"] == row["revenue"] for row in body["annual_projection"])

def test_loan_is_fully_repaid_after_term_and_interest_stops():
    response = client.post(
        "/api/projection",
        json={**payload(), "project_cost": 1_000_000, "debt_pct": 60, "loan_years": 5, "projection_years": 7},
    )
    assert response.status_code == 200
    body = response.json()
    schedule = body["debt_schedule"]

    assert len(schedule) == 7
    assert schedule[4]["closing_balance"] == 0
    assert schedule[5]["opening_balance"] == 0
    assert schedule[5]["principal_repayment"] == 0
    assert schedule[5]["interest_payment"] == 0
    assert schedule[5]["total_debt_service"] == 0
    assert schedule[6]["closing_balance"] == 0
