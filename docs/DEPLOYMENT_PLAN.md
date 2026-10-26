# Deployment plan

1. Build and test the separate API and web frontend in this repository.
2. Create a separate Supabase project after explicit confirmation of the displayed cost estimate.
3. Configure authentication, database schema, row-level security and secrets.
4. Deploy to a newly named Cloudflare staging Worker.
5. Test authentication, project isolation, financial calculations, and Excel/PDF exports.
6. Only after explicit go-live approval, plan a main-domain cutover with DNS backup and rollback steps.

Do not overwrite or delete existing Workers, change production DNS, or change live payments during staging.
