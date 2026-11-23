from app.core.security import api_key_prefix, generate_api_key_plain, hash_api_key, hash_password
from app.models.enums import UserRole
from app.models.lead import ApiKey, Tenant, User
from tests.conftest import requires_db


@requires_db
def test_public_ingest_dedup_and_login_flow(api_client, db_session) -> None:
    tenant = Tenant(slug="test-tenant", name="Test Realty", vertical="real_estate")
    db_session.add(tenant)
    db_session.flush()

    user = User(
        tenant_id=tenant.id,
        email="agent@test.local",
        password_hash=hash_password("TestPass123!"),
        full_name="Test Agent",
        role=UserRole.owner,
    )
    db_session.add(user)

    plain_key = generate_api_key_plain()
    db_session.add(
        ApiKey(
            tenant_id=tenant.id,
            name="Test key",
            key_prefix=api_key_prefix(plain_key),
            key_hash=hash_api_key(plain_key),
            scopes=["leads:write"],
        )
    )
    db_session.flush()

    payload = {
        "full_name": "Ayesha Khan",
        "email": "ayesha@example.com",
        "phone": "+923001234567",
        "enquiry_text": "Looking for a 3-bed apartment in Clifton.",
        "consent_marketing": True,
        "consent_channel_email": True,
    }
    r1 = api_client.post("/v1/public/leads", json=payload, headers={"X-Api-Key": plain_key})
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["duplicate"] is False

    r2 = api_client.post("/v1/public/leads", json=payload, headers={"X-Api-Key": plain_key})
    assert r2.status_code == 200
    assert r2.json()["duplicate"] is True
    assert r2.json()["id"] == body1["id"]

    login = api_client.post(
        "/v1/auth/login",
        json={"tenant_slug": "test-tenant", "email": "agent@test.local", "password": "TestPass123!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    leads = api_client.get("/v1/leads", headers={"Authorization": f"Bearer {token}"})
    assert leads.status_code == 200
    data = leads.json()
    assert data["total"] >= 1
    assert any(item["email"] == "ayesha@example.com" for item in data["items"])

    me = api_client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "agent@test.local"