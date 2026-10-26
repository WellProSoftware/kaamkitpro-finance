from app.model import build_projection


def sample():
    return {
        "project_name": "Sample Pharmacy", "project_type": "Pharmacy",
        "project_cost": 10_000_000, "debt_pct": 50,
        "monthly_revenue": 1_500_000, "growth_pct": 5,
        "variable_cost_pct": 60, "monthly_fixed_cost": 300_000,
        "interest_pct": 10, "loan_years": 5, "projection_years": 5,
    }


def test_debt_and_equity_equal_project_cost():
    result = build_projection(sample())
    assert result["debt"] + result["equity"] == result["project_cost"]


def test_projection_year_count():
    assert len(build_projection(sample())["annual_projection"]) == 5


def test_break_even_is_positive():
    assert build_projection(sample())["annual_projection"][0]["break_even_revenue"] > 0


def test_zero_debt_has_no_dscr_when_no_debt_service():
    data = sample()
    data["debt_pct"] = 0
    result = build_projection(data)
    assert result["debt"] == 0
    assert all(row["dscr"] is None for row in result["annual_projection"])


def test_full_variable_cost_does_not_divide_by_zero():
    data = sample()
    data["variable_cost_pct"] = 100
    result = build_projection(data)
    assert all(row["break_even_revenue"] is None for row in result["annual_projection"])


def test_growth_of_minus_100_percent_keeps_revenue_non_negative():
    data = sample()
    data["growth_pct"] = -100
    result = build_projection(data)
    assert result["annual_projection"][0]["revenue"] > 0
    assert all(row["revenue"] >= 0 for row in result["annual_projection"])


import pytest


@pytest.mark.parametrize("key,value", [
    ("project_cost", float("nan")),
    ("monthly_revenue", float("inf")),
    ("monthly_fixed_cost", -1),
    ("debt_pct", 101),
    ("variable_cost_pct", -1),
    ("interest_pct", 101),
    ("loan_years", 31),
    ("projection_years", 101),
])
def test_rejects_invalid_model_assumptions(key, value):
    data = sample()
    data[key] = value
    with pytest.raises(ValueError):
        build_projection(data)


def test_debt_schedule_reconciles_each_year():
    result = build_projection(sample())
    for row in result["annual_projection"]:
        assert row["opening_debt"] - row["principal"] == row["closing_debt"]
        assert row["interest"] + row["principal"] == row["debt_service"]


def test_loan_is_fully_repaid_at_end_of_tenure():
    data = sample()
    data["projection_years"] = 7
    result = build_projection(data)
    rows = result["annual_projection"]
    assert rows[4]["closing_debt"] == 0
    assert rows[5]["interest"] == 0
    assert rows[5]["principal"] == 0


def test_pre_depreciation_profit_matches_ebitda_less_interest():
    result = build_projection(sample())
    for row in result["annual_projection"]:
        assert row["profit_before_tax_before_depreciation"] == row["ebitda"] - row["interest"]
