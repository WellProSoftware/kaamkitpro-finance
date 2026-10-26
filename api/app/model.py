
def build_projection(data: dict) -> dict:
    """Build a basic annual financial projection in INR."""

    project_cost = float(data.get("project_cost", 0))
    debt_pct = float(data.get("debt_pct", 50)) / 100
    revenue = float(data.get("monthly_revenue", 0)) * 12
    growth = float(data.get("growth_pct", 5)) / 100
    variable_pct = float(data.get("variable_cost_pct", 45)) / 100
    fixed_cost = float(data.get("monthly_fixed_cost", 0)) * 12
    interest_rate = float(data.get("interest_pct", 11)) / 100
    loan_years = max(1, int(data.get("loan_years", 7)))
    years = max(1, min(10, int(data.get("projection_years", 5))))

    debt = project_cost * debt_pct
    equity = project_cost - debt
    annual_principal = debt / loan_years
    results = []

    for year in range(1, years + 1):
        if year > 1:
            revenue *= 1 + growth

        variable_cost = revenue * variable_pct
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
            "break_even_revenue": round(
                fixed_cost / (1 - variable_pct), 2
            ) if variable_pct < 1 else None,
            "cash_after_debt_service": round(
                ebitda - debt_service, 2
            )
        })

    return {
        "currency": "INR",
        "project_cost": round(project_cost, 2),
        "debt": round(debt, 2),
        "equity": round(equity, 2),
        "annual_projection": results,
        "note": "Illustrative projection; further validation is required before bank submission."
    }
