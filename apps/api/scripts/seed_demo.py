"""Seed demo tenant, user, API key, and sample leads.

Usage (from apps/api with Postgres running and migrations applied):

    python scripts/seed_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.core.security import api_key_prefix, generate_api_key_plain, hash_api_key, hash_password
from app.db.session import SessionLocal
from app.models.enums import LeadPriority, LeadStatus, UserRole
from app.models.lead import ApiKey, AutomationSettings, Lead, Tenant, TenantAiConfig, User
from app.schemas.leads import LeadCreate
from app.services import api_keys as api_key_service
from app.services import leads as lead_service
from app.services.qualification import maybe_auto_qualify, run_qualification

DEMO_SLUG = "demo-realty"
DEMO_PASSWORD = "DemoPass123!"


def main() -> None:
    db = SessionLocal()
    try:
        tenant = db.scalar(select(Tenant).where(Tenant.slug == DEMO_SLUG))
        if tenant is None:
            tenant = Tenant(
                slug=DEMO_SLUG,
                name="Vyrenlo Demo Realty",
                vertical="real_estate",
                timezone="Asia/Karachi",
                settings={"owner_email": "owner@demo.local"},
            )
            db.add(tenant)
            db.flush()

        user = db.scalar(
            select(User).where(User.tenant_id == tenant.id, User.email == "owner@demo.local")
        )
        if user is None:
            user = User(
                tenant_id=tenant.id,
                email="owner@demo.local",
                password_hash=hash_password(DEMO_PASSWORD),
                full_name="Demo Owner",
                role=UserRole.owner,
            )
            db.add(user)

        if db.scalar(select(TenantAiConfig).where(TenantAiConfig.tenant_id == tenant.id)) is None:
            db.add(
                TenantAiConfig(
                    tenant_id=tenant.id,
                    qualification_prompt_template=(
                        "Qualify real-estate leads. Extract budget, location, property type, timeline."
                    ),
                    require_approval_for_outbound=False,
                )
            )

        if db.scalar(select(AutomationSettings).where(AutomationSettings.tenant_id == tenant.id)) is None:
            db.add(AutomationSettings(tenant_id=tenant.id))

        existing_keys = db.scalars(select(ApiKey).where(ApiKey.tenant_id == tenant.id)).all()
        plain_key: str | None = None
        if not existing_keys:
            _row, plain_key = api_key_service.create_api_key(
                db, tenant.id, "Website form", ["leads:write"]
            )

        if db.scalar(select(Lead).where(Lead.tenant_id == tenant.id).limit(1)) is None:
            samples = [
                LeadCreate(
                    full_name="Ayesha Khan",
                    email="ayesha.khan@example.com",
                    phone="+923001112233",
                    enquiry_text="Need a 3-bedroom apartment in Clifton, budget 25–35M PKR.",
                    source="website",
                    consent_channel_email=True,
                ),
                LeadCreate(
                    full_name="Omar Farooq",
                    email="omar.f@example.com",
                    enquiry_text="Interested in commercial plot near highway.",
                    source="website",
                ),
            ]
            for sample in samples:
                lead = lead_service.create_lead_manual(db, tenant.id, sample, "seed")
                if maybe_auto_qualify(db, lead) is None:
                    try:
                        run_qualification(db, lead=lead, actor_id="seed")
                    except Exception:
                        if sample.full_name == "Ayesha Khan":
                            lead.priority = LeadPriority.hot
                            lead.status = LeadStatus.qualified

        db.commit()

        print("Demo tenant seeded.")
        print(f"  Tenant slug: {DEMO_SLUG}")
        print(f"  Tenant ID (n8n LEADFLOW_DEMO_TENANT_ID): {tenant.id}")
        print("  Login: owner@demo.local")
        print(f"  Password: {DEMO_PASSWORD}")
        if plain_key:
            print(f"  Public API key (save now): {plain_key}")
        else:
            print("  Public API key: already exists (create a new one via POST /v1/settings/api-keys)")
    except Exception as exc:
        db.rollback()
        raise SystemExit(f"Seed failed: {exc}") from exc
    finally:
        db.close()


if __name__ == "__main__":
    main()