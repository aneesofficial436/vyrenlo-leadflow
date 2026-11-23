from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import ActorType, LeadPriority, LeadStatus
from app.models.lead import Lead, LeadQualification, Tenant, TenantAiConfig
from app.schemas.qualification import QualificationLLMOutput
from app.services.events import record_lead_event
from app.services.follow_ups import schedule_follow_up_sequence

logger = logging.getLogger(__name__)
settings = get_settings()
PROMPT_VERSION = "v1"

JSON_SCHEMA: dict[str, Any] = {
    "name": "lead_qualification",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "category": {"type": "string"},
            "priority": {"type": "string", "enum": ["hot", "warm", "cold"]},
            "intent_score": {"type": "integer", "minimum": 0, "maximum": 100},
            "requirements": {"type": "object"},
            "recommended_action": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": [
            "summary",
            "category",
            "priority",
            "intent_score",
            "requirements",
            "recommended_action",
            "confidence",
        ],
    },
    "strict": True,
}


class QualificationError(Exception):
    pass


def get_ai_config(db: Session, tenant_id: uuid.UUID) -> TenantAiConfig:
    cfg = db.get(TenantAiConfig, tenant_id)
    if cfg is None:
        cfg = TenantAiConfig(tenant_id=tenant_id)
        db.add(cfg)
        db.flush()
    return cfg


def get_latest_qualification(db: Session, lead_id: uuid.UUID) -> LeadQualification | None:
    return db.scalar(
        select(LeadQualification)
        .where(LeadQualification.lead_id == lead_id)
        .order_by(LeadQualification.created_at.desc())
        .limit(1)
    )


def _default_prompt(vertical: str) -> str:
    return f"""You qualify inbound sales leads for a business in the "{vertical}" industry.
Read the enquiry and return structured JSON only.
Extract buyer intent, urgency, budget/location signals when present, and recommend the next sales action.
Priority rules: hot = strong intent + clear requirements + near-term timeline; warm = genuine interest but missing details;
cold = vague, browsing, or unlikely to convert soon."""


def build_messages(*, lead: Lead, tenant: Tenant, template: str) -> list[dict[str, str]]:
    system = template.strip() or _default_prompt(tenant.vertical)
    user_payload = {
        "lead": {
            "full_name": lead.full_name,
            "email": lead.email,
            "phone": lead.phone,
            "source": lead.source,
            "enquiry_text": lead.enquiry_text,
            "metadata": lead.lead_metadata,
        },
        "tenant": {"name": tenant.name, "vertical": tenant.vertical},
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]


def qualify_with_openai(*, messages: list[dict[str, str]], model: str) -> QualificationLLMOutput:
    if not settings.openai_api_key:
        raise QualificationError("openai_api_key_missing")

    url = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "temperature": 0.2,
        "messages": messages,
        "response_format": {"type": "json_schema", "json_schema": JSON_SCHEMA},
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            res = client.post(url, headers=headers, json=body)
    except httpx.HTTPError as exc:
        raise QualificationError("openai_request_failed") from exc

    if res.status_code >= 400:
        logger.warning("OpenAI error status=%s", res.status_code)
        raise QualificationError("openai_error_response")

    data = res.json()
    try:
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return QualificationLLMOutput.model_validate(parsed)
    except (KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
        raise QualificationError("openai_invalid_payload") from exc


def qualify_with_heuristic(*, lead: Lead, tenant: Tenant) -> QualificationLLMOutput:
    text = lead.enquiry_text.lower()
    score = 35
    priority = "cold"
    category = "general_inquiry"

    if tenant.vertical == "real_estate":
        category = "buyer" if any(w in text for w in ("buy", "purchase", "apartment", "house", "plot")) else "inquiry"
        if re.search(r"\d+\s*(m|million|lakh|lac|cr|crore)", text):
            score += 25
        if any(w in text for w in ("clifton", "downtown", "location", "area", "bedroom", "3-bed", "2-bed")):
            score += 15
    if any(w in text for w in ("urgent", "asap", "this week", "ready to", "pre-approved", "cash")):
        score += 20
    if any(w in text for w in ("just browsing", "maybe later", "no rush")):
        score -= 15

    score = max(0, min(100, score))
    if score >= 75:
        priority = "hot"
    elif score >= 50:
        priority = "warm"

    requirements: dict[str, Any] = {}
    budget_match = re.search(r"(\d+\s*[-–]\s*\d+|\d+)\s*(m|million|lakh|lac|cr)?", text, re.I)
    if budget_match:
        requirements["budget_signal"] = budget_match.group(0)

    return QualificationLLMOutput(
        summary=f"{lead.full_name} enquired via {lead.source}. Intent score {score}/100 based on enquiry keywords.",
        category=category,
        priority=priority,  # type: ignore[arg-type]
        intent_score=score,
        requirements=requirements,
        recommended_action="Call within 2 hours" if priority == "hot" else "Send tailored follow-up email",
        confidence=0.55 if settings.qualification_dev_heuristic else 0.7,
    )


def run_qualification(
    db: Session,
    *,
    lead: Lead,
    actor_type: ActorType = ActorType.system,
    actor_id: str | None = None,
) -> LeadQualification:
    tenant = db.get(Tenant, lead.tenant_id)
    if tenant is None:
        raise QualificationError("tenant_not_found")

    cfg = get_ai_config(db, lead.tenant_id)
    lead.status = LeadStatus.qualifying
    messages = build_messages(lead=lead, tenant=tenant, template=cfg.qualification_prompt_template)

    model_used = cfg.qualification_model
    try:
        if settings.openai_api_key:
            output = qualify_with_openai(messages=messages, model=model_used)
        elif settings.qualification_dev_heuristic and settings.environment == "development":
            output = qualify_with_heuristic(lead=lead, tenant=tenant)
            model_used = "heuristic-dev"
        else:
            raise QualificationError("qualification_not_configured")
    except QualificationError:
        lead.status = LeadStatus.new
        record_lead_event(
            db,
            tenant_id=lead.tenant_id,
            lead_id=lead.id,
            event_type="qualification.failed",
            actor_type=actor_type,
            actor_id=actor_id,
        )
        raise

    priority = LeadPriority(output.priority)
    qualification = LeadQualification(
        lead_id=lead.id,
        tenant_id=lead.tenant_id,
        model=model_used,
        prompt_version=PROMPT_VERSION,
        summary=output.summary,
        category=output.category,
        intent_score=output.intent_score,
        priority=priority,
        requirements=output.requirements,
        recommended_action=output.recommended_action,
        raw_response=output.model_dump(),
    )
    db.add(qualification)

    lead.priority = priority
    lead.status = LeadStatus.qualified

    record_lead_event(
        db,
        tenant_id=lead.tenant_id,
        lead_id=lead.id,
        event_type="qualification.completed",
        payload={
            "priority": priority.value,
            "intent_score": output.intent_score,
            "category": output.category,
        },
        actor_type=actor_type,
        actor_id=actor_id,
    )
    schedule_follow_up_sequence(db, lead)
    return qualification


def maybe_auto_qualify(db: Session, lead: Lead) -> LeadQualification | None:
    if settings.n8n_orchestrates_qualification:
        return None
    cfg = get_ai_config(db, lead.tenant_id)
    if not cfg.auto_qualify_on_ingest:
        return None
    try:
        return run_qualification(db, lead=lead)
    except QualificationError:
        logger.info("Auto-qualify skipped for lead_id=%s", lead.id)
        return None