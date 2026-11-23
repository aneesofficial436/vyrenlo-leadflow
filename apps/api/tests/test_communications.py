import uuid

from app.models.enums import CommunicationChannel, CommunicationDirection, CommunicationStatus
from app.models.lead import Lead
from app.services.communications import can_email_lead, create_outbound_email


def test_can_email_requires_consent() -> None:
    lead = Lead(
        tenant_id=uuid.uuid4(),
        full_name="Test",
        email="a@b.com",
        enquiry_text="x",
        dedup_key="k",
        source="web",
        consent_channel_email=False,
    )
    assert not can_email_lead(lead)
    lead.consent_channel_email = True
    assert can_email_lead(lead)


from tests.conftest import requires_db


@requires_db
def test_create_outbound_respects_approval_flag(db_session) -> None:
    from app.models.lead import Tenant, TenantAiConfig

    tenant = Tenant(slug="t", name="T", vertical="real_estate")
    db_session.add(tenant)
    db_session.flush()
    db_session.add(TenantAiConfig(tenant_id=tenant.id, require_approval_for_outbound=True))
    lead = Lead(
        tenant_id=tenant.id,
        full_name="Test",
        email="a@b.com",
        enquiry_text="hello",
        dedup_key="dk",
        source="web",
        consent_channel_email=True,
    )
    db_session.add(lead)
    db_session.flush()
    comm = create_outbound_email(db_session, lead=lead, subject="Hi", body="Body")
    assert comm.status == CommunicationStatus.pending_approval
    assert comm.direction == CommunicationDirection.outbound
    assert comm.channel == CommunicationChannel.email