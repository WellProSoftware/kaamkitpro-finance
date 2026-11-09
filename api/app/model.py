from math import isfinite


def _number(data: dict, key: str, default: float) -> float:
    try:
        value = float(data.get(key, default))
    except (TypeError, ValueError):
        raise ValueError(f"{key} must be a finite number") from None
    if not isfinite(value):
        raise ValueError(f"{key} must be a finite number")
    return value


def _integer(data: dict, key: str, default: int) -> int:
    raw_value = data.get(key, default)
    if isinstance(raw_value, bool):
        raise ValueError(f"{key} must be a whole number")
    try:
        numeric_value = float(raw_value)
    except (TypeError, ValueError):
        raise ValueError(f"{key} must be a whole number") from None
    if not isfinite(numeric_value) or not numeric_value.is_integer():
        raise ValueError(f"{key} must be a whole number")
    return int(numeric_value)


def build_projection(data: dict) -> dict:
    """Build a simplified annual financial projection in INR."""

    project_cost = _number(data, "project_cost", 0)
    debt_pct = _number(data, "debt_pct", 0)
    monthly_revenue = _number(data, "monthly_revenue", 0)
    growth_pct = _number(data, "growth_pct", 0)
    variable_cost_pct = _number(data, "variable_cost_pct", 0)
    monthly_fixed_cost = _number(data, "monthly_fixed_cost", 0)
    interest_pct = _number(data, "interest_pct", 0)
    fixed_cost_inflation_pct = _number(data, "fixed_cost_inflation_pct", 0)
    repayment_method = str(data.get("repayment_method", "equal_annual_principal"))
    loan_years = _integer(data, "loan_years", 1)
    years = _integer(data, "projection_years", 1)

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
    if not 0 <= fixed_cost_inflation_pct <= 100:
        raise ValueError("fixed_cost_inflation_pct must be between 0 and 100")
    if repayment_method not in {"equal_annual_principal", "monthly_emi"}:
        raise ValueError("repayment_method must be equal_annual_principal or monthly_emi")
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
    fixed_cost_inflation = fixed_cost_inflation_pct / 100
    results = []
    monthly_schedule = []
    if repayment_method == "monthly_emi" and debt > 0:
        monthly_rate = interest_rate / 12
        total_months = loan_years * 12
        if monthly_rate == 0:
            emi = debt / total_months
        else:
            factor = (1 + monthly_rate) ** total_months
            emi = debt * monthly_rate * factor / (factor - 1)
        balance = debt
        for month in range(1, total_months + 1):
            opening_balance = balance
            interest_payment = opening_balance * monthly_rate
            principal_payment = min(opening_balance, max(0, emi - interest_payment))
            balance = max(0, opening_balance - principal_payment)
            if month == total_months:
                principal_payment = opening_balance
                balance = 0
            monthly_schedule.append({
                "month": month,
                "year": (month - 1) // 12 + 1,
                "opening_balance": round(opening_balance, 2),
                "emi": round(principal_payment + interest_payment, 2),
                "principal_repayment": round(principal_payment, 2),
                "interest_payment": round(interest_payment, 2),
                "closing_balance": round(balance, 2),
            })

    for year in range(1, years + 1):
        if year > 1:
            revenue *= 1 + growth

        if year > 1:
            fixed_cost *= 1 + fixed_cost_inflation

        variable_cost = revenue * variable_rate
        ebitda = revenue - variable_cost - fixed_cost
        if repayment_method == "monthly_emi":
            year_payments = [item for item in monthly_schedule if item["year"] == year]
            opening_debt = year_payments[0]["opening_balance"] if year_payments else 0
            interest = sum(item["interest_payment"] for item in year_payments)
            principal = sum(item["principal_repayment"] for item in year_payments)
            debt_service = interest + principal
            closing_debt = year_payments[-1]["closing_balance"] if year_payments else 0
        else:
            opening_debt = max(0, debt - annual_principal * (year - 1))
            interest = opening_debt * interest_rate if year <= loan_years else 0
            principal = min(opening_debt, annual_principal) if year <= loan_years else 0
            debt_service = interest + principal
            closing_debt = max(0, opening_debt - principal)

        results.append({
            "year": year,
            "revenue": round(revenue, 2),
            "variable_cost": round(variable_cost, 2),
            "fixed_cost": round(fixed_cost, 2),
            "ebitda": round(ebitda, 2),
            "interest": round(interest, 2),
            "principal": round(principal, 2),
            "opening_debt": round(opening_debt, 2),
            "closing_debt": round(closing_debt, 2),
            "debt_service": round(debt_service, 2),
            "profit_before_tax_before_depreciation": round(ebitda - interest, 2),
            "dscr": round(ebitda / debt_service, 2) if debt_service else None,
            "break_even_revenue": round(fixed_cost / (1 - variable_rate), 2) if variable_rate < 1 else None,
            "cash_after_debt_service": round(ebitda - debt_service, 2),
        })

    return {
        "currency": "INR",
        "model_inputs": {
            "debt_pct": debt_pct,
            "monthly_revenue": monthly_revenue,
            "growth_pct": growth_pct,
            "variable_cost_pct": variable_cost_pct,
            "monthly_fixed_cost": monthly_fixed_cost,
            "interest_pct": interest_pct,
            "fixed_cost_inflation_pct": fixed_cost_inflation_pct,
            "repayment_method": repayment_method,
            "loan_years": loan_years,
            "projection_years": years,
        },
        "project_cost": round(project_cost, 2),
        "debt": round(debt, 2),
        "equity": round(equity, 2),
        "annual_projection": results,
        "monthly_debt_schedule": monthly_schedule,
        "debt_schedule": [
            {"year": row["year"], "opening_balance": row["opening_debt"], "principal_repayment": row["principal"], "interest_payment": row["interest"], "total_debt_service": row["debt_service"], "closing_balance": row["closing_debt"]}
            for row in results
        ],
        "note": "Illustrative projection; validate assumptions and full cash flows before bank submission.",
    }
