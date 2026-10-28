# Finance API

FastAPI backend for KaamKitPro Finance, providing health checks, annual projections, and Excel/PDF report exports.

## Run locally

From this directory:

```bash
python -m venv .venv
```

Activate the environment:
- Windows: `.venv\\Scripts\\activate`
- macOS/Linux: `source .venv/bin/activate`

Then install and start:

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## Frontend CORS configuration

By default, local development origins `http://localhost:3000` and
`http://127.0.0.1:3000` are allowed. For staging, set
`FINANCE_CORS_ORIGINS` to a comma-separated list of exact frontend origins,
for example:

```bash
FINANCE_CORS_ORIGINS=https://your-staging-frontend.example
```

Use the actual staging frontend origin, with no path. Do not use `*` and do
not include the production domain until a separately approved production plan.

## Endpoints

- `GET /health` — health check
- `POST /api/projection` — calculate annual projections
- `POST /api/reports/excel` — download an editable XLSX workbook
- `POST /api/reports/pdf` — download a PDF summary

The request fields and validation rules are visible in the FastAPI docs at `/docs`.

### Itemized project costs

All three POST endpoints accept an optional `itemized_costs` object. When supplied, its
values become the project cost used by the projection, debt/equity split, Excel workbook,
and PDF report. Values are INR amounts and must be finite and non-negative; the total
must not exceed INR 1,000,000,000,000,000. Unknown category names are rejected with HTTP 422.

Supported category names are exact and case-sensitive:

- `Outsourcing`
- `Warehouse setup`
- `Hospital setup / expansion`
- `Retail / pharmacy setup or expansion`
- `Optical setup or expansion`
- `Equipment and technology`
- `Licences, deposits and professional fees`
- `Initial inventory and working capital`
- `Other project costs`

Example request fragment:

```json
{
  "project_cost": 3500000,
  "debt_pct": 60,
  "itemized_costs": {
    "Outsourcing": 1500000,
    "Warehouse setup": 2000000
  }
}
```

In this example, itemized costs override `project_cost` and produce a total project cost
of INR 3,500,000, debt of INR 2,100,000, and equity of INR 1,400,000. Categories omitted
from the object are treated as zero in the Excel cost breakdown. If `itemized_costs` is
omitted, the API uses the supplied aggregate `project_cost` as before.

## Container

Build from this directory:

```bash
docker build -t kaamkitpro-finance-api .
docker run --rm -p 8000:8000 kaamkitpro-finance-api
```

## Tests

```bash
python -m pytest -q
```

## Limitations and security

This is an early planning tool, not audited accounts or a lender-approved project report. Tax, depreciation, working capital, detailed cash flow, and full loan amortisation need validation before external financial use. Never commit service-role keys, passwords, or other secrets.
