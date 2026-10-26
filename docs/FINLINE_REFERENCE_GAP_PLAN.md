# Finline-inspired product gap plan

## Goal
Use Finline (https://www.finline.in/) as a product-quality benchmark for guided project-report creation while keeping KaamKitPro Finance's own identity, existing financial model, and existing features. Do not copy Finline's branding, wording, page layout, proprietary report templates, or claims.

## Existing KaamKitPro Finance features to preserve (do not duplicate)
- Editable project assumptions and project types
- Annual revenue / EBITDA / debt-service / DSCR / break-even / cash-after-debt projection
- Browser-local draft save and restore
- CSV export
- API-backed Excel and PDF export actions (API URL still needs staging configuration)
- API endpoints for projection, XLSX, and PDF reports
- Configurable projection horizon (1–100 years)

## Reference features and current gaps
1. Guided project-report workflow — not implemented; current screen is a single assumptions dashboard.
2. Project profile details (promoter, location, products/services, capacity, employment) — not implemented.
3. Detailed projected Profit & Loss, Balance Sheet, and Cash Flow statements — not implemented as a complete statement set.
4. Detailed loan repayment schedule with opening balance, principal, interest, and closing balance — only simplified annual debt service exists.
5. Means of finance and project-cost breakdown — only total cost and debt/equity percentages exist.
6. Break-even and ratio analysis — a simplified break-even and DSCR exist; other ratios and validation checks are missing.
7. CMA/bank-scheme-specific report formats — not implemented and must not be represented as bank-approved until validated against the applicable bank/scheme format.
8. Editable multi-section report preview and repeatable report generation — not implemented.
9. Persistent, account-linked project storage — local browser storage only; Supabase project persistence/auth is not connected.
10. Staging verification — build, API tests, and real XLSX/PDF download smoke tests still need to be run and recorded.

## Recommended implementation order
1. Complete the core financial engine: yearly P&L, debt amortisation schedule, and consistency checks; add tests.
2. Build a project-cost and means-of-finance breakdown without replacing the existing total-cost/debt/equity inputs.
3. Add projected Balance Sheet and Cash Flow with clearly documented assumptions.
4. Add project profile and sector-specific optional fields, keeping the existing project types.
5. Generate an editable report preview and consistent Excel/PDF exports from the same validated model.
6. Add persistent project saving only after auth and row-level security are tested.
7. Validate scheme-specific outputs against official current templates before offering them as bank/scheme reports.
8. Deploy and test on separate staging hosting; do not touch production domain, DNS, old Workers, or live payments without explicit approval.

## Acceptance criteria
- Existing dashboard and CSV export continue working.
- New features extend rather than duplicate existing controls and outputs.
- All financial statements use one shared model and reconcile where applicable.
- Tests cover zero-debt, no-profit, negative cash flow, fully depreciated assets (once depreciation exists), and long projections.
- No claim of passing tests, bank acceptance, or live deployment without evidence.
