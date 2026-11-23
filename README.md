# Vyrenlo AI LeadFlow

AI-powered lead management and follow-up automation for Vyrenlo’s automation agency portfolio.

| Doc | Description |
|-----|-------------|
| [DELIVERABLES.md](DELIVERABLES.md) | Phase 1–9 checklist |
| [docs/architecture.md](docs/architecture.md) | System design |
| [docs/architecture-diagram.md](docs/architecture-diagram.md) | Mermaid diagrams |
| [docs/deployment.md](docs/deployment.md) | Production deploy |
| [docs/demo-script.md](docs/demo-script.md) | Sales demo walkthrough |
| [docs/security.md](docs/security.md) | Security controls |

**Status:** All 9 phases complete (portfolio-ready MVP).

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- Optional: Python 3.12+, Node 22+ for local dev without full Compose

## Quick start (development)

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml --env-file .env up --build -d
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| n8n | http://localhost:5678 |
| Mailpit | http://localhost:8025 |

```bash
cd apps/api
alembic upgrade head   # if not using API container migrate
python scripts/seed_demo.py
```

**Login:** `demo-realty` · `owner@demo.local` · `DemoPass123!`

## Production-style stack

```bash
cp .env.production.example .env
# edit secrets
docker compose -f docker/docker-compose.prod.yml --env-file .env up -d --build
```

## Verify & demo helpers

```powershell
# Windows
.\scripts\verify_stack.ps1
$env:LEADFLOW_DEMO_API_KEY = "lf_live_..."
.\scripts\run_demo.ps1
```

## Local dev (API / web only)

See previous sections in git history or [deployment.md](docs/deployment.md) for split API + `npm run dev` workflow.

## Save to Cursor (Origin)

Native Windows needs **WSL** for the `origin` CLI. See [docs/cursor-origin-push.md](docs/cursor-origin-push.md) and `scripts/push-to-cursor-origin.sh` (run inside WSL).

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) — pytest (Postgres + Redis) + Next.js build.

## Tests

```bash
cd apps/api && pip install -r requirements.txt && pytest
```

## Project layout

```
vyrenlo-leadflow/
  apps/api/              FastAPI, Alembic, tests
  apps/web/              Next.js CRM
  automation/n8n/        Workflow JSON + README
  docker/                compose dev + prod
  docs/                  architecture, demo, deploy, security
  scripts/               seed, verify_stack, run_demo
```

## Environment variables

- Development: [.env.example](.env.example)
- Production: [.env.production.example](.env.production.example)

## Roadmap

| Phase | Status |
|-------|--------|
| 1–9 | **Complete** |