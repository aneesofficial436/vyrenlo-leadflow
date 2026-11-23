from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from app.core.config import get_settings


def sign_payload(payload: dict[str, Any]) -> str:
    settings = get_settings()
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    digest = hmac.new(settings.webhook_signing_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"