"""initial schema

Revision ID: 20251123_0001
Revises:
Create Date: 2025-11-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20251123_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = postgresql.ENUM("owner", "admin", "agent", "viewer", name="user_role", create_type=False)
lead_status = postgresql.ENUM(
    "new",
    "qualifying",
    "qualified",
    "contacted",
    "engaged",
    "won",
    "lost",
    "spam",
    "opted_out",
    name="lead_status",
    create_type=False,
)
lead_priority = postgresql.ENUM("hot", "warm", "cold", "unqualified", name="lead_priority", create_type=False)
communication_channel = postgresql.ENUM("email", "whatsapp", "internal", name="communication_channel", create_type=False)
communication_direction = postgresql.ENUM("inbound", "outbound", name="communication_direction", create_type=False)
communication_status = postgresql.ENUM(
    "draft",
    "pending_approval",
    "sent",
    "failed",
    "received",
    name="communication_status",
    create_type=False,
)
follow_up_status = postgresql.ENUM(
    "scheduled",
    "sent",
    "skipped",
    "cancelled",
    "failed",
    name="follow_up_status",
    create_type=False,
)
actor_type = postgresql.ENUM("system", "user", "n8n", "lead", name="actor_type", create_type=False)


def upgrade() -> None:
    op.execute("CREATE TYPE user_role AS ENUM ('owner', 'admin', 'agent', 'viewer')")
    op.execute(
        "CREATE TYPE lead_status AS ENUM ('new', 'qualifying', 'qualified', 'contacted', "
        "'engaged', 'won', 'lost', 'spam', 'opted_out')"
    )
    op.execute("CREATE TYPE lead_priority AS ENUM ('hot', 'warm', 'cold', 'unqualified')")
    op.execute("CREATE TYPE communication_channel AS ENUM ('email', 'whatsapp', 'internal')")
    op.execute("CREATE TYPE communication_direction AS ENUM ('inbound', 'outbound')")
    op.execute(
        "CREATE TYPE communication_status AS ENUM ('draft', 'pending_approval', 'sent', 'failed', 'received')"
    )
    op.execute(
        "CREATE TYPE follow_up_status AS ENUM ('scheduled', 'sent', 'skipped', 'cancelled', 'failed')"
    )
    op.execute("CREATE TYPE actor_type AS ENUM ('system', 'user', 'n8n', 'lead')")

    op.create_table(
        "tenants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("vertical", sa.String(length=64), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )
    op.create_index(op.f("ix_users_tenant_id"), "users", ["tenant_id"], unique=False)
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)
    op.create_table(
        "api_keys",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("key_prefix", sa.String(length=16), nullable=False),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.String()), server_default="{}", nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_keys_tenant_id"), "api_keys", ["tenant_id"], unique=False)
    op.create_table(
        "tenant_ai_config",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("qualification_model", sa.String(length=64), nullable=False),
        sa.Column("qualification_prompt_template", sa.Text(), nullable=False),
        sa.Column("response_model", sa.String(length=64), nullable=False),
        sa.Column("auto_qualify_on_ingest", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("require_approval_for_outbound", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("tenant_id"),
    )
    op.create_table(
        "automation_settings",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("follow_up_intervals_hours", postgresql.ARRAY(sa.Integer()), server_default="{24,72,168}", nullable=False),
        sa.Column("max_follow_ups", sa.Integer(), server_default="3", nullable=False),
        sa.Column("business_hours", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("n8n_webhook_base", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("tenant_id"),
    )
    op.create_table(
        "leads",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("source_detail", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("enquiry_text", sa.Text(), nullable=False),
        sa.Column("status", lead_status, nullable=False),
        sa.Column("priority", lead_priority, nullable=False),
        sa.Column("assigned_user_id", sa.UUID(), nullable=True),
        sa.Column("consent_marketing", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("consent_channel_email", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("consent_channel_whatsapp", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("dedup_key", sa.String(length=128), nullable=False),
        sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_follow_up_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("follow_up_paused", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "dedup_key", name="uq_leads_tenant_dedup"),
    )
    op.create_index("ix_leads_tenant_created", "leads", ["tenant_id", "created_at"], unique=False)
    op.create_index("ix_leads_tenant_next_follow_up", "leads", ["tenant_id", "next_follow_up_at"], unique=False)
    op.create_index("ix_leads_tenant_priority_status", "leads", ["tenant_id", "priority", "status"], unique=False)
    op.create_index(op.f("ix_leads_tenant_id"), "leads", ["tenant_id"], unique=False)
    op.create_table(
        "lead_qualifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("lead_id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("intent_score", sa.SmallInteger(), nullable=False),
        sa.Column("priority", lead_priority, nullable=False),
        sa.Column("requirements", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("recommended_action", sa.String(length=255), nullable=False),
        sa.Column("raw_response", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lead_qualifications_lead_id"), "lead_qualifications", ["lead_id"], unique=False)
    op.create_index(op.f("ix_lead_qualifications_tenant_id"), "lead_qualifications", ["tenant_id"], unique=False)
    op.create_table(
        "communications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("lead_id", sa.UUID(), nullable=False),
        sa.Column("channel", communication_channel, nullable=False),
        sa.Column("direction", communication_direction, nullable=False),
        sa.Column("subject", sa.String(length=512), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", communication_status, nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("ai_generated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("approved_by_user_id", sa.UUID(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_communications_lead_created", "communications", ["lead_id", "created_at"], unique=False)
    op.create_index(op.f("ix_communications_lead_id"), "communications", ["lead_id"], unique=False)
    op.create_index(op.f("ix_communications_tenant_id"), "communications", ["tenant_id"], unique=False)
    op.create_table(
        "follow_ups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("lead_id", sa.UUID(), nullable=False),
        sa.Column("sequence_step", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", follow_up_status, nullable=False),
        sa.Column("communication_id", sa.UUID(), nullable=True),
        sa.Column("cancellation_reason", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["communication_id"], ["communications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_follow_ups_lead_id"), "follow_ups", ["lead_id"], unique=False)
    op.create_index(op.f("ix_follow_ups_tenant_id"), "follow_ups", ["tenant_id"], unique=False)
    op.create_table(
        "lead_notes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("lead_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lead_notes_lead_id"), "lead_notes", ["lead_id"], unique=False)
    op.create_index(op.f("ix_lead_notes_tenant_id"), "lead_notes", ["tenant_id"], unique=False)
    op.create_table(
        "lead_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("lead_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("actor_type", actor_type, nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_lead_events_idempotency"),
    )
    op.create_index("ix_lead_events_tenant_created", "lead_events", ["tenant_id", "created_at"], unique=False)
    op.create_index(op.f("ix_lead_events_lead_id"), "lead_events", ["lead_id"], unique=False)
    op.create_index(op.f("ix_lead_events_tenant_id"), "lead_events", ["tenant_id"], unique=False)
    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("workflow_name", sa.String(length=128), nullable=False),
        sa.Column("n8n_execution_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_runs_tenant_id"), "workflow_runs", ["tenant_id"], unique=False)
    op.create_table(
        "ingestion_idempotency",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("lead_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_ingestion_tenant_key"),
    )


def downgrade() -> None:
    op.drop_table("ingestion_idempotency")
    op.drop_table("workflow_runs")
    op.drop_table("lead_events")
    op.drop_table("lead_notes")
    op.drop_table("follow_ups")
    op.drop_table("communications")
    op.drop_table("lead_qualifications")
    op.drop_table("leads")
    op.drop_table("automation_settings")
    op.drop_table("tenant_ai_config")
    op.drop_table("api_keys")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.drop_table("tenants")
    op.execute("DROP TYPE IF EXISTS actor_type")
    op.execute("DROP TYPE IF EXISTS follow_up_status")
    op.execute("DROP TYPE IF EXISTS communication_status")
    op.execute("DROP TYPE IF EXISTS communication_direction")
    op.execute("DROP TYPE IF EXISTS communication_channel")
    op.execute("DROP TYPE IF EXISTS lead_priority")
    op.execute("DROP TYPE IF EXISTS lead_status")
    op.execute("DROP TYPE IF EXISTS user_role")