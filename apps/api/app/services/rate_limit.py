from __future__ import annotations

from fastapi import HTTPException, status

from app.services.redis_client import get_redis

PUBLIC_LIMIT_PER_MINUTE = 60
LOGIN_LIMIT_PER_MINUTE = 10


def _enforce_bucket(*, bucket: str, limit: int, window_seconds: int) -> None:
    try:
        redis = get_redis()
        count = redis.incr(bucket)
        if count == 1:
            redis.expire(bucket, window_seconds)
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
    except HTTPException:
        raise
    except Exception:
        pass


def enforce_public_rate_limit(*, tenant_id: str, api_key_id: str) -> None:
    _enforce_bucket(
        bucket=f"rl:public:{tenant_id}:{api_key_id}",
        limit=PUBLIC_LIMIT_PER_MINUTE,
        window_seconds=60,
    )


def enforce_login_rate_limit(*, client_key: str) -> None:
    _enforce_bucket(
        bucket=f"rl:login:{client_key}",
        limit=LOGIN_LIMIT_PER_MINUTE,
        window_seconds=60,
    )