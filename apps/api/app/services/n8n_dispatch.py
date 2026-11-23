from __future__ import annotations

import logging
import uuid
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.webhook_signing import sign_payload

logger = logging.getLogger(__name__)


EVENT_WEBHOOK_ENV: dict[str, str] = {
    "lead.created": "n8n_webhook_lead_created",
    "qualification.completed": "n8n_webhook_qualification_completed",
    "qualification.failed": "n8n_webhook_qualification_failed",
    "follow_up.due": "n8n_webhook_follow_up_due",
}


def resolve_webhook_url(event_type: str) -> str | None:
    settings = get_settings()
    attr = EVENT_WEBHOOK_ENV.get(event_type)
    if not attr:
        return None
    url = getattr(settings, attr, None)
    return url.strip() if url else None


def dispatch_to_n8n(
    *,
    event_type: str,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> bool:
    url = resolve_webhook_url(event_type)
    if not url:
        return False

    body = {
        "event_type": event_type,
        "tenant_id": str(tenant_id),
        "lead_id": str(lead_id) if lead_id else None,
        "payload": payload or {},
    }
    headers = {
        "Content-Type": "application/json",
        "X-LeadFlow-Event": event_type,
        "X-Webhook-Signature": sign_payload(body),
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.post(url, json=body, headers=headers)
        if res.status_code >= 400:
            logger.warning("n8n webhook failed event=%s status=%s", event_type, res.status_code)
            return False
        return True
    except httpx.HTTPError:
        logger.exception("n8n webhook error event=%s", event_type)
        return False


def schedule_n8n_event(
    background_tasks: Any,
    *,
    event_type: str,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> None:
    if background_tasks is None:
        dispatch_to_n8n(
            event_type=event_type,
            tenant_id=tenant_id,
            lead_id=lead_id,
            payload=payload,
            idempotency_key=idempotency_key,
        )
        return

    background_tasks.add_task(
        dispatch_to_n8n,
        event_type=event_type,
        tenant_id=tenant_id,
        lead_id=lead_id,
        payload=payload,
        idempotency_key=idempotency_key,
    )