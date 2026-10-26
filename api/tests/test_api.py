from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def payload():
    return {
        "project_name": "Test Pharmacy",
        "project_type": "Pharmacy",
        "project_cost": 1000000,
        "debt_pct": 60,
        "monthly_revenue": 150000,
        "growth_pct": 5,
        "variable_cost_pct": 55,
        "monthly_fixed_cost": 25000,
        "interest_pct": 11,
        "loan_years": 5,
        "projection_years": 3,
    }


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


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
