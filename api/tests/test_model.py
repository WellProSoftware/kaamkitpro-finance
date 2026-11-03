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
    ("project_cost", None),
    ("monthly_revenue", "not-a-number"),
    ("monthly_revenue", float("inf")),
    ("monthly_fixed_cost", -1),
    ("debt_pct", 101),
    ("variable_cost_pct", -1),
    ("interest_pct", 101),
    ("loan_years", 31),
    ("projection_years", 101),
    ("loan_years", 2.5),
    ("projection_years", 3.5),
    ("loan_years", True),
    ("projection_years", float("inf")),
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


def test_operating_model_reconciles_revenue_costs_and_ebitda():
    """Revenue less variable and fixed costs must equal EBITDA each year."""
    result = build_projection(sample())
    for row in result["annual_projection"]:
        assert row["revenue"] - row["variable_cost"] - row["fixed_cost"] == row["ebitda"]


def test_cash_after_debt_service_reconciles_ebitda_and_debt_service():
    """Cash metric is deliberately pre-tax and pre-capex."""
    result = build_projection(sample())
    for row in result["annual_projection"]:
        assert row["ebitda"] - row["debt_service"] == row["cash_after_debt_service"]


def test_dscr_uses_ebitda_divided_by_total_debt_service():
    result = build_projection(sample())
    for row in result["annual_projection"]:
        if row["debt_service"]:
            assert row["dscr"] == round(row["ebitda"] / row["debt_service"], 2)
        else:
            assert row["dscr"] is None


def test_revenue_growth_compounds_from_prior_year():
    data = sample()
    data["projection_years"] = 4
    data["growth_pct"] = 10
    rows = build_projection(data)["annual_projection"]
    assert [row["revenue"] for row in rows] == [
        18_000_000, 19_800_000, 21_780_000, 23_958_000
    ]


def test_public_debt_schedule_matches_projection_and_stops_after_payoff():
    data = sample()
    data["loan_years"] = 3
    data["projection_years"] = 6
    result = build_projection(data)

    assert len(result["debt_schedule"]) == 6
    for schedule_row, projection_row in zip(result["debt_schedule"], result["annual_projection"]):
        assert schedule_row["year"] == projection_row["year"]
        assert schedule_row["opening_balance"] == projection_row["opening_debt"]
        assert schedule_row["principal_repayment"] == projection_row["principal"]
        assert schedule_row["interest_payment"] == projection_row["interest"]
        assert schedule_row["total_debt_service"] == projection_row["debt_service"]
        assert schedule_row["closing_balance"] == projection_row["closing_debt"]

    assert all(row["closing_balance"] == 0 for row in result["debt_schedule"][2:])
    assert all(row["total_debt_service"] == 0 for row in result["debt_schedule"][3:])


@pytest.mark.parametrize(
    "data,expected_ebitda,expected_break_even",
    [
        ({"monthly_revenue": 0, "monthly_fixed_cost": 100_000}, -1_200_000, 3_000_000),
        ({"monthly_revenue": 100_000, "monthly_fixed_cost": 0}, 480_000, 0),
    ],
)
def test_zero_revenue_or_fixed_cost_edge_cases(data, expected_ebitda, expected_break_even):
    inputs = sample()
    inputs.update(data)
    row = build_projection(inputs)["annual_projection"][0]
    assert row["ebitda"] == expected_ebitda
    assert row["break_even_revenue"] == expected_break_even


def test_negative_ebitda_produces_negative_dscr_when_debt_service_exists():
    inputs = sample()
    inputs.update({"monthly_revenue": 0, "monthly_fixed_cost": 100_000})
    row = build_projection(inputs)["annual_projection"][0]
    assert row["ebitda"] < 0
    assert row["debt_service"] > 0
    assert row["dscr"] < 0


def test_fixed_cost_inflation_compounds_annually():
    data = sample()
    data.update({"projection_years": 3, "fixed_cost_inflation_pct": 10})
    rows = build_projection(data)["annual_projection"]
    assert [row["fixed_cost"] for row in rows] == [3_600_000, 3_960_000, 4_356_000]
    assert [row["ebitda"] for row in rows] == [3_600_000, 3_240_000, 2_844_000]


def test_fixed_cost_inflation_defaults_to_zero():
    data = sample()
    data["projection_years"] = 3
    rows = build_projection(data)["annual_projection"]
    assert [row["fixed_cost"] for row in rows] == [3_600_000] * 3
