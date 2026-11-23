# n8n workflow specifications

## Shared conventions

- **Idempotency:** API sends `Idempotency-Key` on outbound webhooks; n8n should forward on internal callbacks when retrying.
- **Auth:** `X-Service-Token` on every LeadFlow internal HTTP node.
- **Logging:** `POST /v1/internal/workflow-runs` records `n8n_execution_id`, `status`, `error_message`.
- **Errors:** WF 07 (Error Trigger) captures failed executions across the LeadFlow folder.

---

### 1. New Lead Capture

| | |
|--|--|
| **Trigger** | Webhook `POST /webhook/lead-created` (from API `lead.created`) |
| **Nodes** | Webhook → Log workflow run → IF not duplicate |
| **Output** | Ready to chain qualify (manual link to WF02 or HTTP node) |
| **Errors** | Non-2xx from log node → Error workflow |

### 2. AI Lead Qualification

| | |
|--|--|
| **Trigger** | Webhook `POST /webhook/qualify-lead` (manual or called from WF01) |
| **Body** | `{ "lead_id", "tenant_id" }` |
| **API** | `POST /v1/internal/leads/{id}/qualify?tenant_id=` |
| **Output** | Qualification JSON; API fires `qualification.completed` webhook |
| **Retry** | HTTP Request node: 3 tries, 5s wait |

### 3. Lead Notification

| | |
|--|--|
| **Trigger** | Webhook `qualification-completed` (from API) |
| **Logic** | IF `payload.priority == hot` → `staff-notify` |
| **Consent** | Full email draft/send in Phase 7 |

### 4. Automated Follow-up Scheduler

| | |
|--|--|
| **Trigger** | Schedule every hour |
| **API** | `GET /v1/internal/follow-ups/due?tenant_id=` |
| **Phase 7** | Loop items → generate message → send |

### 5. Customer Response Detection

| | |
|--|--|
| **Trigger** | Webhook `inbound-message` (email provider relay in Phase 7) |
| **Now** | Logs workflow run; pause follow-ups in Phase 7 |

### 6. Daily Sales Summary

| | |
|--|--|
| **Trigger** | Cron 08:00 UTC |
| **API** | `GET /v1/internal/daily-summary?tenant_id=` |
| **Phase 7** | Email owner distribution |

### 7. Failed Workflow Recovery

| | |
|--|--|
| **Trigger** | n8n Error Trigger |
| **Action** | `POST /v1/internal/workflow-runs` with `status: failed` |
| **Ops** | Alert channel to be added in Phase 8 |