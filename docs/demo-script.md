# LeadFlow live demo script (~12 minutes)

Audience: real-estate agency owner or ops manager.  
Goal: show capture → AI qualify → notify → follow-up → reply → dashboard.

## Before the meeting

1. Stack running (`docker compose -f docker/docker-compose.yml --env-file .env up -d`).
2. `python scripts/seed_demo.py` in `apps/api`.
3. n8n workflows **01, 03, 04** active; variables set (`LEADFLOW_SERVICE_TOKEN`, `LEADFLOW_DEMO_TENANT_ID`).
4. Mailpit open: http://localhost:8025  
5. Dashboard: http://localhost:3000/login (`demo-realty` / `owner@demo.local` / `DemoPass123!`).

## Scene 1 — The problem (30s)

Explain: leads from the website sit in email; hot buyers get a slow reply; no pipeline view.

## Scene 2 — New enquiry (2 min)

Submit a **hot** lead via API (use seeded API key):

```bash
curl -s -X POST http://localhost:8000/v1/public/leads \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: YOUR_KEY" \
  -d "{\"full_name\":\"Sara Ahmed\",\"email\":\"sara.demo@example.com\",\"phone\":\"+923001112233\",\"enquiry_text\":\"Urgent: 3-bed in Clifton, budget 25-35M PKR, pre-approved. Need viewing this week.\",\"consent_channel_email\":true}"
```

**Show:** API returns `{ duplicate: false }`; n8n execution for workflow 01/03; activity on dashboard.

## Scene 3 — AI qualification (2 min)

Open **Leads** → Sara Ahmed → **AI qualification** panel (Hot, intent score, recommended action).

Optional: click **Re-qualify** to show manual re-run.

## Scene 4 — Staff alert (1 min)

**Mailpit:** email to `owner@demo.local` “Hot lead: Sara Ahmed” (workflow 03).

## Scene 5 — CRM control (2 min)

Change status, pause follow-ups toggle, add an internal note.  
If `require_approval_for_outbound=true`, show **Approvals** page.

## Scene 6 — Follow-up automation (2 min)

Explain scheduled steps (24h / 72h / 168h).  
Trigger WF04 manually in n8n or call:

```bash
curl -X POST "http://localhost:8000/v1/internal/leads/{LEAD_ID}/follow-ups/execute?tenant_id={TENANT_ID}" \
  -H "X-Service-Token: YOUR_INTERNAL_TOKEN"
```

**Mailpit:** outbound follow-up to Sara (if consent + intervals due).

## Scene 7 — Customer replies (1 min)

```bash
curl -s -X POST http://localhost:8000/v1/internal/inbound-email \
  -H "Content-Type: application/json" \
  -H "X-Service-Token: YOUR_INTERNAL_TOKEN" \
  -d "{\"tenant_id\":\"{TENANT_ID}\",\"from_email\":\"sara.demo@example.com\",\"subject\":\"Re: Clifton\",\"body\":\"Thursday 4pm works for me.\"}"
```

**Show:** Lead status **engaged**, follow-ups paused, communication history inbound row.

## Scene 8 — Executive view (1 min)

**Overview:** total leads, hot count, follow-ups due, sources.  
**Close:** Vyrenlo can deploy this as a managed automation package for their agency.

## Talking points

- Tenant-isolated SaaS shape; real estate first, vertical config later.
- OpenAI + approval gates for brand-safe outbound.
- n8n for schedules and integrations without redeploying code.