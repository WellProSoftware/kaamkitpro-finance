import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .model import build_projection
from .reports import build_excel_report, build_pdf_report

app = FastAPI(title="KaamKitPro Finance API", version="0.3.0")

# Configure explicit staging frontend origins via FINANCE_CORS_ORIGINS.
# Keep localhost available for local development; do not use wildcard origins.
_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
_allowed_origins = [
    origin.strip()
    for origin in os.getenv("FINANCE_CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class ProjectionInput(BaseModel):
    project_name: str = Field(default="New Project", max_length=120)
    project_type: str = Field(default="Other", max_length=80)
    project_cost: float = Field(default=0, ge=0, le=1_000_000_000_000_000)
    debt_pct: float = Field(default=50, ge=0, le=100)
    monthly_revenue: float = Field(default=0, ge=0, le=1_000_000_000_000_000)
    growth_pct: float = Field(default=5, ge=-100, le=500)
    variable_cost_pct: float = Field(default=45, ge=0, le=100)
    monthly_fixed_cost: float = Field(default=0, ge=0, le=1_000_000_000_000_000)
    interest_pct: float = Field(default=11, ge=0, le=100)
    loan_years: int = Field(default=7, ge=1, le=30)
    projection_years: int = Field(default=5, ge=1, le=100)


def make_projection(data: ProjectionInput) -> dict[str, Any]:
    result = build_projection(data.model_dump())
    result["project_name"] = data.project_name
    result["project_type"] = data.project_type
    return result


@app.get("/health")
def health():
    return {"status": "ok", "service": "kaamkitpro-finance-api", "version": app.version}


@app.get("/")
def root():
    return {
        "service": "KaamKitPro Finance API",
        "docs": "/docs",
        "health": "/health",
        "endpoints": ["/api/projection", "/api/reports/excel", "/api/reports/pdf"],
    }


def validated_projection(data: ProjectionInput) -> dict[str, Any]:
    try:
        return make_projection(data)
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Unable to calculate projection from the supplied assumptions.",
        ) from exc


@app.post("/api/projection")
def projection(data: ProjectionInput):
    return validated_projection(data)


@app.post("/api/reports/excel")
def excel_report(data: ProjectionInput):
    result = validated_projection(data)
    return Response(
        content=build_excel_report(result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="kaamkitpro-finance-projection.xlsx"'},
    )


@app.post("/api/reports/pdf")
def pdf_report(data: ProjectionInput):
    result = validated_projection(data)
    return Response(
        content=build_pdf_report(result),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="kaamkitpro-finance-projection.pdf"'},
    )
