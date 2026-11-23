# AI lead qualification (Phase 5)

## Flow

1. Lead ingested (`POST /v1/public/leads` or CRM create).
2. If `tenant_ai_config.auto_qualify_on_ingest` is true, qualification runs inline.
3. Result stored in `lead_qualifications`; `leads.priority` and `leads.status` updated.
4. Event `qualification.completed` (or `qualification.failed`) written to `lead_events`.

## Manual / n8n

| Endpoint | Auth |
|----------|------|
| `POST /v1/leads/{id}/qualify` | JWT (agent+) |
| `POST /v1/internal/leads/{id}/qualify?tenant_id=` | `X-Service-Token` |

## Configuration

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Enables live OpenAI structured JSON qualification |
| `OPENAI_BASE_URL` | Optional proxy / Azure-compatible base URL |
| `QUALIFICATION_DEV_HEURISTIC` | `true` + `ENVIRONMENT=development` uses keyword heuristic when no API key |

Per-tenant: `tenant_ai_config` (`qualification_model`, prompt template, `auto_qualify_on_ingest`).

## Response contract

See `QualificationLLMOutput` in `app/schemas/qualification.py` — summary, category, priority, intent_score, requirements JSON, recommended_action, confidence.