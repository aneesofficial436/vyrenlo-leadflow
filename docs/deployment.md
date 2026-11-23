# Deployment guide (Phase 9)

## Environments

| File | Purpose |
|------|---------|
| `docker/docker-compose.yml` | Local development (reload, Mailpit, volume mounts) |
| `docker/docker-compose.prod.yml` | Demo/staging/production-style (2 workers, built web image) |
| `.env.production.example` | Production secret checklist |

## Production bootstrap

1. Copy `.env.production.example` → `.env` and replace every `CHANGE_ME`.
2. Point DNS / TLS termination (Caddy, nginx, Cloudflare) to API `:8000`, web `:3000`, n8n `:5678`.
3. Set `NEXT_PUBLIC_API_URL` to the **browser-reachable** API URL (HTTPS).
4. Configure real SMTP (SendGrid, Resend, SES). Disable Mailpit.
5. Set `OPENAI_API_KEY` and `QUALIFICATION_DEV_HEURISTIC=false`.
6. Run:
```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env up -d --build
```
7. Seed once (from host with `DATABASE_URL` or `docker compose exec api python scripts/seed_demo.py`).
8. Import and activate n8n workflows; set `LEADFLOW_SERVICE_TOKEN` and tenant UUID in n8n variables.

## Backups

- Postgres: nightly `pg_dump` of volume `leadflow_pg_data` (or managed RDS).
- n8n: backup volume `leadflow_n8n_data`.

## Health checks

- Liveness: `GET /health`
- Readiness: `GET /ready` (DB + Redis)
- Internal: `GET /v1/internal/health` with `X-Service-Token`

## Pre-go-live checklist

- [ ] Unique `JWT_SECRET`, `INTERNAL_SERVICE_TOKEN`, `WEBHOOK_SIGNING_SECRET`, `N8N_ENCRYPTION_KEY`
- [ ] `EXPOSE_OPENAPI=false`
- [ ] `CORS_ORIGINS` and `TRUSTED_HOSTS` match public URLs
- [ ] TLS on all public endpoints
- [ ] OpenAI + SMTP credentials in secret store (not git)
- [ ] Rate limits via Redis (managed Redis in prod)
- [ ] n8n webhooks active; error workflow (07) enabled
- [ ] CI green on `main`

## Scaling notes

- API: increase Uvicorn `--workers` or run multiple replicas behind a load balancer (sticky sessions not required).
- Workers: outbound email and n8n handle async work; keep qualification synchronous unless you add a queue later.
- Multi-tenant: single DB with `tenant_id`; for large SaaS, consider Postgres RLS and per-tenant rate limits.