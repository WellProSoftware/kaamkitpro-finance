# Finance API staging deployment guide

## Current safety boundary

Deploy only the API as a **separate Cloudflare Python Worker** named `kaamkitpro-finance-api-staging`. Do not change the production domain, production Worker, DNS records, payment settings, or the existing placeholder staging Worker.

The repository includes a Cloudflare Python Workers entry point at `api/worker.py`, configuration at `api/wrangler.toml`, and dependency manifest at `api/pyproject.toml`. Cloudflare documents FastAPI support through its ASGI adapter: https://developers.cloudflare.com/workers/languages/python/packages/fastapi/

## Deploy to a new staging Worker

From the repository root, install `uv` and Node.js, then run:

```bash
cd api
uv run pywrangler dev
```

Test locally before deploying. When local checks pass and your Cloudflare CLI is authenticated to the correct account:

```bash
uv run pywrangler deploy
```

This configuration targets only `kaamkitpro-finance-api-staging`. Before deployment, confirm the selected Cloudflare account and Worker name. Do not use the existing `kaamkitpro-finance-staging` name or any production Worker.

## Required staging validation

Verify all of the following before connecting the frontend:

- `GET /health` returns JSON with status `ok`.
- `GET /docs` loads the API documentation.
- `POST /api/projection` returns the expected number of annual rows.
- `POST /api/reports/excel` returns an XLSX file that opens correctly.
- `POST /api/reports/pdf` returns a PDF file that opens correctly.
- Browser CORS requests work from the exact staging frontend origin.

The Excel/PDF libraries must be confirmed compatible with Cloudflare's Python Workers runtime during local preview and deployment. If either library fails to import or generate files, do not route frontend traffic to this Worker; investigate a compatible implementation first.

## Environment and CORS

The current configuration allows the existing Finance staging Worker origin only. If the frontend is hosted at a different origin, update `FINANCE_CORS_ORIGINS` to the exact HTTPS origin before testing. Do not use `*` and do not add the production website without explicit approval.

The API does not require Supabase keys for calculation or report export. Do not add service-role keys. Supabase project persistence and authenticated access are separate follow-up tasks.

## Financial-model interpretation

The current loan schedule uses equal annual principal repayments, with interest calculated on the opening balance. It is not a monthly EMI schedule. The profit-before-tax indicator is EBITDA less interest and excludes depreciation and tax; do not present it as net profit. These are planning estimates, not audited financial statements or bank-approved DPRs.

## Go-live gate

Do not connect the frontend until the API has been deployed and the full staging smoke-test sequence has passed. Do not change production domain, DNS, payment settings, or old Workers as part of this work.
