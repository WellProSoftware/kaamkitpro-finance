from fastapi import FastAPI
from pydantic import BaseModel, Field

from .model import build_projection

app = FastAPI(title="Professional Projection Software API", version="0.1.0")


class ProjectionInput(BaseModel):
    project_name: str = Field(default="New Project", max_length=120)
    project_type: str = "Other"
    project_cost: float = Field(default=0, ge=0)
    debt_pct: float = Field(default=50, ge=0, le=100)
    monthly_revenue: float = Field(default=0, ge=0)
    growth_pct: float = Field(default=5, ge=-100, le=500)
    variable_cost_pct: float = Field(default=45, ge=0, le=100)
    monthly_fixed_cost: float = Field(default=0, ge=0)
    interest_pct: float = Field(default=11, ge=0, le=100)
    loan_years: int = Field(default=7, ge=1, le=30)
    projection_years: int = Field(default=5, ge=1, le=10)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/projection")
def projection(data: ProjectionInput):
    result = build_projection(data.model_dump())
    result["project_name"] = data.project_name
    result["project_type"] = data.project_type
    return result
