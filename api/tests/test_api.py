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
