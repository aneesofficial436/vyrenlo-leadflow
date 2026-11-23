# Security (Phase 8)

## Authentication & authorization

- JWT access tokens (short TTL) + refresh token rotation stored hashed in Postgres.
- RBAC: `owner`, `admin`, `agent`, `viewer`.
- Internal/n8n routes: `X-Service-Token` header (constant-time comparison via equality).
- Public ingest: API key hashed at rest; scopes enforced.

## Tenant isolation

Every CRM query filters `tenant_id` from the JWT. Cross-tenant access returns **404** (see `tests/test_tenant_isolation.py`).

## Rate limiting (Redis)

| Bucket | Limit |
|--------|--------|
| Public ingest per API key | 60/min |
| Login per IP + tenant | 10/min |

Fails **open** if Redis is unreachable (availability over strict limiting in dev).

## Transport & headers

- CORS restricted to configured origins; limited methods/headers.
- `SecurityHeadersMiddleware`: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, etc.
- Optional `TrustedHostMiddleware` via `TRUSTED_HOSTS=host1,host2`.

## Secrets & logging

- No API keys or passwords in logs; access logs use path + status only.
- `X-Request-ID` on every response for tracing.
- Set `EXPOSE_OPENAPI=false` in production to hide `/docs`.

## Webhooks

Outbound n8n events signed with `X-Webhook-Signature` (HMAC-SHA256). Idempotency keys on events and public ingest.

## CI

GitHub Actions workflow `.github/workflows/leadflow-ci.yml` runs migrations + pytest (Postgres/Redis) and Next.js production build.