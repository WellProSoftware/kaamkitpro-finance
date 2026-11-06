"""Indicative India funding-route catalogue.

Rules are screening prompts, not eligibility decisions. Re-check live scheme circulars
and lender product terms before every application or report issue.
"""
from typing import Any

SCHEMES: list[dict[str, Any]] = [
    {
        "id": "cgtmse",
        "name": "CGTMSE Credit Guarantee Scheme",
        "route": "Bank / eligible lender credit with guarantee cover",
        "loan_min": 0,
        "loan_max": 100_000_000,
        "fit": "Eligible new or existing micro and small enterprises; Udyam registration is required for a new guarantee application.",
        "key_conditions": [
            "The enterprise and activity must be eligible under the current CGTMSE scheme.",
            "Apply to a CGTMSE Member Lending Institution; the lender sanctions credit and files the guarantee application.",
            "Guarantee cover is not a subsidy, direct loan, waiver, or promise of sanction.",
            "The lender assesses viability, repayment capacity, promoter contribution and credit history.",
        ],
        "screening": "Potential route where the borrower is an eligible MSE and the requested facility is within the current scheme ceiling.",
        "official_url": "https://www.cgtmse.in/",
        "source_checked": "2026-11-06",
        "status": "Current scheme; lender confirmation required",
    },
    {
        "id": "mudra",
        "name": "Pradhan Mantri MUDRA Yojana (PMMY)",
        "route": "Participating bank / NBFC / MFI",
        "loan_min": 0,
        "loan_max": 2_000_000,
        "fit": "Income-generating micro enterprises in manufacturing, trading, services and permitted allied activities.",
        "key_conditions": [
            "Shishu: up to ₹50,000; Kishore: above ₹50,000 to ₹5 lakh; Tarun: above ₹5 lakh to ₹10 lakh.",
            "Tarun Plus: above ₹10 lakh to ₹20 lakh only for entrepreneurs who previously availed and successfully repaid a Tarun loan.",
            "Term loan and working capital may be considered; lender appraisal and product terms apply.",
            "No uniform interest rate or guaranteed sanction is implied by the scheme ceiling.",
        ],
        "screening": "Amount-based indicative match; Tarun Plus requires successful prior Tarun repayment.",
        "official_url": "https://financialservices.gov.in/pradhan-mantri-mudra-yojana-pmmy",
        "source_checked": "2026-11-06",
        "status": "Current scheme; lender confirmation required",
    },
    {
        "id": "pmegp",
        "name": "Prime Minister's Employment Generation Programme (PMEGP)",
        "route": "KVIC / KVIB / DIC channel and financing bank",
        "loan_min": 0,
        "loan_max": 5_000_000,
        "fit": "Eligible new micro-enterprises in the non-farm sector; project ceiling differs by manufacturing vs service/business.",
        "key_conditions": [
            "New projects only under the new-unit route; existing units and expansion are generally not eligible under that route.",
            "Published project ceilings: ₹50 lakh manufacturing and ₹20 lakh service/business for margin-money subsidy.",
            "Beneficiary contribution and subsidy rates vary by category and rural/urban location.",
            "Subsidy is back-ended and subject to scheme process, bank sanction, verification and lock-in conditions; do not net it off as cash on day one.",
        ],
        "screening": "Potential match only for a new eligible micro-enterprise; classify activity and applicant category before calculating subsidy.",
        "official_url": "https://www.kviconline.gov.in/pmegpeportal/",
        "source_checked": "2026-11-06",
        "status": "Current guidelines must be checked on application date",
    },
    {
        "id": "stand_up_india_legacy",
        "name": "Stand-Up India (legacy scheme reference)",
        "route": "Scheduled Commercial Bank; confirm successor programme status",
        "loan_min": 1_000_000,
        "loan_max": 10_000_000,
        "fit": "Legacy scheme targeted women and SC/ST entrepreneurs for greenfield enterprises.",
        "key_conditions": [
            "The Department of Financial Services page states the original scheme period was up to 31 March 2025.",
            "A successor first-time entrepreneur scheme was announced in Budget 2025-26; implementation status and final operating guidelines must be confirmed.",
            "Do not treat legacy loan limits or conditions as an open current application route without bank confirmation.",
        ],
        "screening": "Shown for reference only; not presented as currently open.",
        "official_url": "https://www.financialservices.gov.in/stand-india-scheme-supi",
        "source_checked": "2026-11-06",
        "status": "Legacy scheme period ended; successor status to be verified",
    },
    {
        "id": "private_debt",
        "name": "Private debt / NBFC / structured finance",
        "route": "Bank, NBFC or private credit provider",
        "loan_min": 0,
        "loan_max": None,
        "fit": "Established or new businesses with a credible use of funds, repayment source, promoter support and acceptable risk profile.",
        "key_conditions": [
            "Terms are provider-specific: interest, fees, security, covenants, tenor, moratorium and prepayment must be compared.",
            "Model the effective annual cost and monthly repayment from the lender's Key Facts Statement / sanction terms.",
            "Avoid unregistered lenders and advance-fee intermediaries; verify the regulated entity and contract.",
        ],
        "screening": "Custom lender quote required; no universal rate or eligibility threshold is assumed.",
        "official_url": "https://www.rbi.org.in/",
        "source_checked": "2026-11-06",
        "status": "Commercial route; due diligence required",
    },
    {
        "id": "equity_investor",
        "name": "Angel / strategic / private equity investor",
        "route": "Equity or convertible instrument, subject to legal structuring",
        "loan_min": 0,
        "loan_max": None,
        "fit": "Projects with scalable market opportunity, credible team, defensible economics and clear capital deployment milestones.",
        "key_conditions": [
            "Equity is not debt: there is no fixed EMI, but ownership dilution, governance rights and exit expectations apply.",
            "Prepare cap table, valuation rationale, use-of-funds milestones, unit economics, downside case and investor return scenarios.",
            "Convertible notes, CCPS and other instruments require company-law, tax and securities-law review.",
        ],
        "screening": "Investor-readiness route; not a loan eligibility decision.",
        "official_url": "https://www.startupindia.gov.in/",
        "source_checked": "2026-11-06",
        "status": "Private negotiation; no assured funding",
    },
]

def list_funding_routes() -> dict[str, Any]:
    return {
        "as_of": "2026-11-06",
        "currency": "INR",
        "disclaimer": (
            "Indicative screening information only. Scheme rules, caps, eligible activities, "
            "rates and application windows can change. Final eligibility and sanction are "
            "determined by the implementing agency or lender. Confirm official guidelines "
            "before relying on this information."
        ),
        "routes": SCHEMES,
    }
