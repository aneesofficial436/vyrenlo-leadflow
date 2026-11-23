# Vyrenlo AI LeadFlow — deliverables checklist

| # | Deliverable | Location |
|---|-------------|----------|
| 1 | Functional application | `apps/api`, `apps/web` |
| 2 | n8n automation | `automation/n8n/workflows/*.json` |
| 3 | Database schema & migrations | `apps/api/alembic/versions/` |
| 4 | API documentation | `/docs` when `EXPOSE_OPENAPI=true`; OpenAPI at `/openapi.json` |
| 5 | Docker deployment | `docker/docker-compose.yml`, `docker/docker-compose.prod.yml` |
| 6 | Sample data | `apps/api/scripts/seed_demo.py` |
| 7 | Automated tests | `apps/api/tests/`, CI workflow |
| 8 | Setup README | `README.md` |
| 9 | Architecture diagram | `docs/architecture-diagram.md` |
| 10 | Demo scenario | `docs/demo-script.md`, `scripts/run_demo.ps1` |

Additional references: [security.md](docs/security.md), [deployment.md](docs/deployment.md), [ai-qualification.md](docs/ai-qualification.md).