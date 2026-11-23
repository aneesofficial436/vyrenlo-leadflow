from app.services.webhook_signing import sign_payload


def test_sign_payload_is_stable() -> None:
    payload = {"event_type": "lead.created", "tenant_id": "abc", "lead_id": "def", "payload": {}}
    a = sign_payload(payload)
    b = sign_payload(payload)
    assert a == b
    assert a.startswith("sha256=")