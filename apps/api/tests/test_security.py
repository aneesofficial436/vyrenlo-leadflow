import uuid

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.services.leads import compute_dedup_key, normalize_email, normalize_phone


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("DemoPass123!")
    assert verify_password("DemoPass123!", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_access_token_payload() -> None:
    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, tenant_id=tenant_id, role="owner")
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["role"] == "owner"
    assert payload["type"] == "access"


def test_dedup_key_stable_per_email() -> None:
    tenant = uuid.uuid4()
    a = compute_dedup_key(tenant, "Jane@Example.COM", None)
    b = compute_dedup_key(tenant, normalize_email("jane@example.com"), None)
    assert a == b


def test_normalize_phone_strips_formatting() -> None:
    assert normalize_phone("+1 (555) 123-4567") == "15551234567"