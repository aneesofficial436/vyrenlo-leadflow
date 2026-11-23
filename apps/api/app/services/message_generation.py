from __future__ import annotations

import json

import httpx

from app.core.config import get_settings
from app.models.lead import Lead, LeadQualification


def generate_follow_up_email(
    *,
    lead: Lead,
    step: int,
    qualification: LeadQualification | None,
) -> tuple[str, str]:
    settings = get_settings()
    summary = qualification.summary if qualification else lead.enquiry_text[:280]
    subject = f"Re: your enquiry — {lead.full_name.split()[0] if lead.full_name else 'there'}"

    if settings.openai_api_key:
        try:
            return _generate_openai(lead=lead, step=step, summary=summary, subject=subject)
        except Exception:
            pass

    return subject, _heuristic_body(lead=lead, step=step, summary=summary)


def _heuristic_body(*, lead: Lead, step: int, summary: str) -> str:
    name = lead.full_name.split()[0] if lead.full_name else "there"
    if step <= 1:
        return (
            f"Hi {name},\n\n"
            f"Thank you for reaching out. I reviewed your enquiry and wanted to follow up personally.\n\n"
            f"Summary: {summary}\n\n"
            f"Could you share a convenient time for a quick call this week?\n\n"
            f"Best regards,\nVyrenlo Realty Team"
        )
    return (
        f"Hi {name},\n\n"
        f"Just checking in on your property search (follow-up {step}). "
        f"If your plans have changed, simply reply and we will update our notes.\n\n"
        f"Best regards,\nVyrenlo Realty Team"
    )


def _generate_openai(*, lead: Lead, step: int, summary: str, subject: str) -> tuple[str, str]:
    settings = get_settings()
    url = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    prompt = (
        f"Write a short professional follow-up email (plain text, under 180 words) for step {step}. "
        f"Lead name: {lead.full_name}. Summary: {summary}. "
        f"Return JSON with keys subject and body."
    )
    body = {
        "model": "gpt-4o-mini",
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=45.0) as client:
        res = client.post(url, headers=headers, json=body)
    res.raise_for_status()
    content = json.loads(res.json()["choices"][0]["message"]["content"])
    return content.get("subject", subject), content.get("body", _heuristic_body(lead=lead, step=step, summary=summary))