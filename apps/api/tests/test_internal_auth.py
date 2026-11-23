from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_internal_routes_require_service_token() -> None:
    res = client.get("/v1/internal/health")
    assert res.status_code == 403

    res = client.get("/v1/internal/health", headers={"X-Service-Token": "wrong"})
    assert res.status_code == 403