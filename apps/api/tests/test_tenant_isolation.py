from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.lead import Tenant, User
from app.services import leads as lead_service
from app.schemas.leads import LeadCreate
from tests.conftest import requires_db


@requires_db
def test_lead_not_visible_across_tenants(api_client, db_session) -> None:
    t1 = Tenant(slug="iso-a", name="A", vertical="real_estate")
    t2 = Tenant(slug="iso-b", name="B", vertical="real_estate")
    db_session.add_all([t1, t2])
    db_session.flush()

    u1 = User(
        tenant_id=t1.id,
        email="a@iso.local",
        password_hash=hash_password("TestPass123!"),
        full_name="A User",
        role=UserRole.owner,
    )
    db_session.add(u1)

    lead = lead_service.create_lead_manual(
        db_session,
        t2.id,
        LeadCreate(
            full_name="Secret",
            email="secret@other.com",
            enquiry_text="Cross-tenant probe",
        ),
        "seed",
    )
    db_session.flush()

    login = api_client.post(
        "/v1/auth/login",
        json={"tenant_slug": "iso-a", "email": "a@iso.local", "password": "TestPass123!"},
    )
    token = login.json()["access_token"]
    res = api_client.get(f"/v1/leads/{lead.id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404