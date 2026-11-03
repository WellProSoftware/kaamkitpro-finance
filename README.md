# Professional Projection Software

An editable INR financial projection and project-report application for hospital, pharmacy, optical, retail, warehouse, manufacturing and other project types.

## Features
- Project cost, debt and equity funding estimates
- Annual revenue, expense and EBITDA projections
- Indicative profit-before-tax calculation before depreciation
- Equal annual principal repayment and opening-balance interest schedule
- DSCR, break-even revenue, Excel and PDF exports
- Aggregate or itemized project-cost planning

## Projection methodology
- Year 1 revenue equals monthly revenue multiplied by 12. Later years apply the same annual growth assumption.
- Variable costs are a fixed percentage of revenue. Monthly fixed costs are annualized and held constant.
- EBITDA equals revenue less variable costs and fixed costs.
- Debt and equity are based on project cost and the debt-funding percentage.
- Principal is repaid in equal annual installments over the loan term. Interest is calculated on opening debt.
- DSCR equals EBITDA divided by interest plus principal; it is blank when debt service is zero.
- Break-even revenue equals annual fixed costs divided by the contribution margin. It is undefined at a 100% variable-cost ratio.
- Cash after debt service equals EBITDA less interest and principal. This is pre-tax and pre-capex, not free cash flow.

## Important limitations
The current model excludes depreciation, income tax, GST, working-capital movements, inventory cycles, capex replacement, seasonality, monthly cash flows, fixed-cost inflation, changing margins, grace periods, balloon payments, EMI repayment and a detailed balance sheet. It is not a complete cash-flow statement, audited financial statement, bank-approved DPR, credit decision or guarantee of returns.

Hospital, pharmacy, optical and retail expansion may need location-wise sales, customer volumes, pricing, staffing, inventory and ramp-up assumptions. Add and validate these drivers before relying on the forecast for a funding decision.

## Excel workbook guide
- **Executive Summary:** key funding and forecast indicators.
- **Model Inputs:** editable assumptions. Yellow cells are intended inputs; the calculated project-cost cell is formula-driven.
- **Project Cost Breakdown:** editable categories. All cost categories start at zero. Enter project-specific estimates; no sample project values are preloaded.
- **Assumptions:** formula-driven annual forecast and debt schedule.
- **Read Me:** workbook usage and limitations.

Select **Itemized costs** in Model Inputs to use the Project Cost Breakdown total. **Aggregate input** uses the aggregate project-cost value instead. Excel recalculates formulas when opened. Worksheet protection helps prevent accidental formula edits; it is not password security. Workbook-only edits are not automatically reflected in a separately generated PDF; submit updated assumptions again to create an updated report.

## Validation
Application inputs are range-checked, with Excel data validation where supported. Reconcile project costs against quotations and have a qualified finance professional validate full project cash flows before sharing with a lender or investor.

## Development and safety
This project is developed and tested separately before production website changes. No deployment is performed by this repository workflow. Never commit passwords, API keys, access tokens or other secrets. Keep the production website, DNS, production analytics and live payments unchanged during development.
