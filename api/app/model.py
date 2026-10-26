from math import isfinite


def _number(data: dict, key: str, default: float) -> float:
    value = float(data.get(key, default))
    if not isfinite(value):
        raise ValueError(f"{key} must be a finite number")
    return value


def build_projection(data: dict) -> dict:
    """Build a simplified annual financial projection in INR."""

    project_cost = _number(data, "project_cost", 0)
    debt_pct = _number(data, "debt_pct", 50)
    monthly_revenue = _number(data, "monthly_revenue", 0)
    growth_pct = _number(data, "growth_pct", 5)
    variable_cost_pct = _number(data, "variable_cost_pct", 45)
    monthly_fixed_cost = _number(data, "monthly_fixed_cost", 0)
    interest_pct = _number(data, "interest_pct", 11)
    loan_years = int(data.get("loan_years", 7))
    years = int(data.get("projection_years", 5))

    if project_cost < 0 or monthly_revenue < 0 or monthly_fixed_cost < 0:
        raise ValueError("Project cost, monthly revenue, and fixed costs cannot be negative")
    if not 0 <= debt_pct <= 100:
        raise ValueError("debt_pct must be between 0 and 100")
    if not -100 <= growth_pct <= 500:
        raise ValueError("growth_pct must be between -100 and 500")
    if not 0 <= variable_cost_pct <= 100:
        raise ValueError("variable_cost_pct must be between 0 and 100")
    if not 0 <= interest_pct <= 100:
        raise ValueError("interest_pct must be between 0 and 100")
    if not 1 <= loan_years <= 30:
        raise ValueError("loan_years must be between 1 and 30")
    if not 1 <= years <= 100:
        raise ValueError("projection_years must be between 1 and 100")

    debt = project_cost * debt_pct / 100
    equity = project_cost - debt
    annual_principal = debt / loan_years
    revenue = monthly_revenue * 12
    growth = growth_pct / 100
    variable_rate = variable_cost_pct / 100
    fixed_cost = monthly_fixed_cost * 12
    interest_rate = interest_pct / 100
    results = []

    for year in range(1, years + 1):
        if year > 1:
            revenue *= 1 + growth

        variable_cost = revenue * variable_rate
        ebitda = revenue - variable_cost - fixed_cost
        opening_debt = max(0, debt - annual_principal * (year - 1))
        interest = opening_debt * interest_rate if year <= loan_years else 0
        principal = min(opening_debt, annual_principal) if year <= loan_years else 0
        debt_service = interest + principal

        results.append({
            "year": year,
            "revenue": round(revenue, 2),
            "variable_cost": round(variable_cost, 2),
            "fixed_cost": round(fixed_cost, 2),
            "ebitda": round(ebitda, 2),
            "interest": round(interest, 2),
            "principal": round(principal, 2),
            "dscr": round(ebitda / debt_service, 2) if debt_service else None,
            "break_even_revenue": round(fixed_cost / (1 - variable_rate), 2) if variable_rate < 1 else None,
            "cash_after_debt_service": round(ebitda - debt_service, 2),
        })

    return {
        "currency": "INR",
        "project_cost": round(project_cost, 2),
        "debt": round(debt, 2),
        "equity": round(equity, 2),
        "annual_projection": results,
        "note": "Illustrative projection; validate assumptions and full cash flows before bank submission.",
    }
