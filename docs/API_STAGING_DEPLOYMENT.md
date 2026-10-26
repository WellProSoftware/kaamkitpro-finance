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

The current API does not require Supabase keys for calculation or report export. Do not add service-role keys to the container. Supabase project persistence and authenticated access are separate follow-up tasks.

## Go-live gate

Before any production cutover, confirm CI passes, test all endpoints against staging, verify downloads open correctly, validate access controls and financial assumptions, and obtain explicit approval. This guide does not itself deploy the API.
