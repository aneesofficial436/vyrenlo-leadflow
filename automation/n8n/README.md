# LeadFlow n8n automation (Phase 6)

## Quick start

1. Start stack: `docker compose -f docker/docker-compose.yml up -d`
2. Open n8n: http://localhost:5678
3. Set n8n **environment variables** (Settings → Variables):
   - `LEADFLOW_SERVICE_TOKEN` — same as API `INTERNAL_SERVICE_TOKEN`
   - `LEADFLOW_DEMO_TENANT_ID` — UUID of demo tenant (from DB after seed)
4. Import each JSON under `workflows/` (**Workflow → Import from file**)
5. **Activate** workflows 01, 02, 03 (webhook triggers)

## API → n8n events

After a new lead (non-duplicate), the API `POST`s to configured webhooks with HMAC header `X-Webhook-Signature`.

| Event | Webhook path | Env variable |
|-------|----------------|--------------|
| `lead.created` | `/webhook/lead-created` | `N8N_WEBHOOK_LEAD_CREATED` |
| `qualification.completed` | `/webhook/qualification-completed` | `N8N_WEBHOOK_QUALIFICATION_COMPLETED` |
| `qualification.failed` | `/webhook/qualification-failed` | `N8N_WEBHOOK_QUALIFICATION_FAILED` |

Body shape:

```json
{
  "event_type": "lead.created",
  "tenant_id": "uuid",
  "lead_id": "uuid",
  "payload": { "source": "website" }
}
```

## n8n → API (internal routes)

All require header `X-Service-Token: <INTERNAL_SERVICE_TOKEN>`.

| Route | Used by |
|-------|---------|
| `POST /v1/internal/leads/{id}/qualify?tenant_id=` | WF 02 |
| `GET /v1/internal/leads/{id}?tenant_id=` | Extensions |
| `POST /v1/internal/leads/{id}/staff-notify?tenant_id=` | WF 03 |
| `GET /v1/internal/follow-ups/due?tenant_id=` | WF 04 |
| `GET /v1/internal/daily-summary?tenant_id=` | WF 06 |
| `POST /v1/internal/workflow-runs` | WF 01, 05, 07 |

Docker network hostname for API: `http://api:8000` (used in workflow JSON).

## Orchestration modes

| `N8N_ORCHESTRATES_QUALIFICATION` | Behavior |
|----------------------------------|----------|
| `false` (default) | API auto-qualifies on ingest; n8n handles notifications & schedules |
| `true` | API skips auto-qualify; chain WF 01 → call WF 02 or internal qualify |

## Workflow reference

See [docs/n8n-workflows.md](../../docs/n8n-workflows.md) for triggers, nodes, idempotency, and error handling per workflow.