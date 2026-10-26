# Finance API staging deployment guide

## Current safety boundary

Deploy only the API container to a separate staging service. Do not change the production domain, production Worker, DNS records, or payment settings as part of staging validation.

## Container build

Build from the repository root:

```bash
docker build -t kaamkitpro-finance-api:staging api
```

Run locally for a smoke test:

```bash
docker run --rm -p 8000:8000 kaamkitpro-finance-api:staging
```

Then verify:
- `GET /health` returns `{"status":"ok",...}`
- `GET /docs` loads API documentation
- `POST /api/projection` returns annual projections
- `POST /api/reports/excel` returns an XLSX file
- `POST /api/reports/pdf` returns a PDF file

## Staging hosting requirements

Use a dedicated service named for KaamKitPro Finance staging, configured to build from `api/Dockerfile` with build context `api`. Expose the container's HTTP port 8000. Use only staging credentials and do not set production secrets. If a health-check path is configurable, set it to `/health`.

Do not connect a custom production domain. Keep the existing Cloudflare Finance staging Worker separate until the API has been deployed and tested; then configure a staging-only API URL in the frontend.

## Environment variables and secrets

Set `FINANCE_CORS_ORIGINS` to the exact HTTPS origin of the staging frontend, for example `https://<your-finance-staging-frontend-host>`. Do not include paths, do not use `*`, and do not include the production website unless it is explicitly approved. Local development defaults are `http://localhost:3000` and `http://127.0.0.1:3000`.

The current API does not require Supabase keys for calculation or report export. Do not add service-role keys to the container. Supabase project persistence and authenticated access are separate follow-up tasks.

## Financial-model interpretation

The current loan schedule uses equal annual principal repayments, with interest calculated on the opening balance. It is not a monthly EMI schedule. The profit-before-tax indicator is EBITDA less interest and excludes depreciation and tax; do not present it as net profit. These are planning estimates, not audited financial statements or bank-approved DPRs.

## Staging smoke-test sequence

After deploying the API to its dedicated staging host, record the staging API base URL and check the following without changing DNS or the existing production Worker:

1. Open `<staging-api-url>/health` and confirm the JSON status is `ok`.
2. Open `<staging-api-url>/docs` and confirm the API schema loads.
3. Submit a small sample payload to `/api/projection`; confirm the number of annual rows matches `projection_years` and debt balances reconcile.
4. Request `/api/reports/excel` and `/api/reports/pdf`; download and open both files.
5. From the staging frontend, confirm requests work only after setting the exact frontend origin in `FINANCE_CORS_ORIGINS`.
6. Record results and logs before treating staging as verified.

## Go-live gate

Before any production cutover, confirm CI passes, test all endpoints against staging, verify downloads open correctly, validate access controls and financial assumptions, and obtain explicit approval. This guide does not itself deploy the API.
