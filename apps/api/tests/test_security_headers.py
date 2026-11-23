from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_security_headers_present() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-Request-ID")