from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://leadflow:leadflow@localhost:5432/leadflow"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "dev-only-change-me"
    jwt_issuer: str = "vyrenlo-leadflow"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    cors_origins: str = "http://localhost:3000"

    webhook_signing_secret: str = "dev-webhook-secret"
    internal_service_token: str = "dev-internal-token"

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    qualification_dev_heuristic: bool = True

    n8n_orchestrates_qualification: bool = False
    n8n_webhook_lead_created: str | None = None
    n8n_webhook_qualification_completed: str | None = None
    n8n_webhook_qualification_failed: str | None = None
    n8n_webhook_follow_up_due: str | None = None

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "noreply@leadflow.local"
    smtp_use_tls: bool = False

    expose_openapi: bool = True
    trusted_hosts: str = ""

    @property
    def trusted_host_list(self) -> list[str]:
        return [h.strip() for h in self.trusted_hosts.split(",") if h.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()