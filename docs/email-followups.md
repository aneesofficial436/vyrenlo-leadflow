# Email & follow-ups (Phase 7)

## SMTP

Configure `SMTP_*` in `.env`. Docker Compose points the API at **Mailpit** (`localhost:8025` UI).

## Consent

Outbound email requires `lead.consent_channel_email` and a valid `lead.email`.

## Approval

`tenant_ai_config.require_approval_for_outbound`:

- `true` → follow-ups create `pending_approval` communications; approve in CRM **Approvals** or via API.
- `false` → follow-ups send immediately (demo seed default).

## Lifecycle

1. **Qualification** → `schedule_follow_up_sequence()` sets `follow_ups` rows and `next_follow_up_at`.
2. **n8n WF04** → lists due leads → `POST /v1/internal/leads/{id}/follow-ups/execute`.
3. **Execute** → AI/heuristic body → communication → SMTP send (or pending approval).
4. **Inbound** → `POST /v1/internal/inbound-email` → pauses follow-ups, status `engaged`.

## CRM API

| Method | Path |
|--------|------|
| GET | `/v1/communications/pending-approval` |
| GET | `/v1/communications/leads/{lead_id}` |
| POST | `/v1/communications/{id}/approve` |
| POST | `/v1/communications/{id}/send` |