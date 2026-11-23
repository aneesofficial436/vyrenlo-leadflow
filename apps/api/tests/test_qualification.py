import uuid

import pytest

from app.models.lead import Lead, Tenant
from app.services.qualification import qualify_with_heuristic


@pytest.mark.parametrize(
    "enquiry,expected_priority",
    [
        ("Urgent — need 3-bed in Clifton, budget 25-35 million, pre-approved.", "hot"),
        ("Maybe interested in an apartment someday.", "cold"),
    ],
)
def test_heuristic_priority(enquiry: str, expected_priority: str) -> None:
    tenant = Tenant(slug="x", name="Demo", vertical="real_estate")
    tenant.id = uuid.uuid4()
    lead = Lead(
        tenant_id=tenant.id,
        full_name="Test",
        enquiry_text=enquiry,
        dedup_key="abc",
        source="website",
    )
    out = qualify_with_heuristic(lead=lead, tenant=tenant)
    if expected_priority == "hot":
        assert out.priority in ("hot", "warm")
        assert out.intent_score >= 50
    else:
        assert out.priority == "cold"