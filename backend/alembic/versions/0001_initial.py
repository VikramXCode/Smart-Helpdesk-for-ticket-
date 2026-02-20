"""Initial migration – creates all tables.

Revision ID: 0001
Revises:
Create Date: 2026-02-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension (requires superuser or pg_extension privilege)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # companies
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("plan_tier", sa.String(50), nullable=False, server_default="Basic"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # teams (forward reference – created before users due to FK)
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("company_id", "name", name="uq_team_company_name"),
    )

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("employee", "it_staff", "company_admin", "super_admin", name="user_role"), nullable=False, server_default="employee"),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="offline"),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("company_id", "email", name="uq_user_company_email"),
    )

    # company_team_mappings
    op.create_table(
        "company_team_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("team_name", sa.String(255), nullable=False),
        sa.UniqueConstraint("company_id", "category", name="uq_mapping_company_category"),
    )

    # knowledge_articles
    op.create_table(
        "knowledge_articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("view_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("embedding", sa.Text, nullable=True),  # vector stored as text, cast in queries
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # tickets
    op.create_table(
        "tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ticket_number", sa.String(20), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.Enum("new", "assigned", "in_progress", "pending", "resolved", "closed", "auto_resolved", name="ticket_status"), nullable=False, server_default="new"),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("priority", sa.Enum("low", "medium", "high", "critical", name="ticket_priority"), nullable=False, server_default="medium"),
        sa.Column("assigned_team", sa.String(255), nullable=True),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.Enum("web", "chat", "email", "mobile", "glpi", "solman", name="ticket_source"), nullable=False, server_default="web"),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("embedding", sa.Text, nullable=True),
        sa.Column("suggested_article_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_articles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ai_suggestion", sa.Text, nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ticket_messages
    op.create_table(
        "ticket_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("author_type", sa.String(20), nullable=False, server_default="user"),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("is_internal", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # notifications_config
    op.create_table(
        "notifications_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.Enum("ticket_created", "ticket_assigned", "ticket_resolved", "ticket_escalated", name="notification_event"), nullable=False),
        sa.Column("email_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("sms_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("email_recipients", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("sms_recipients", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.UniqueConstraint("company_id", "event_type", name="uq_notif_company_event"),
    )

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("details", postgresql.JSON, nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # trend_clusters
    op.create_table(
        "trend_clusters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ticket_ids", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("ticket_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Indexes for common query patterns
    op.create_index("ix_tickets_company_status", "tickets", ["company_id", "status"])
    op.create_index("ix_tickets_company_created", "tickets", ["company_id", "created_at"])
    op.create_index("ix_tickets_assigned_to", "tickets", ["assigned_to"])
    op.create_index("ix_audit_logs_company", "audit_logs", ["company_id", "timestamp"])
    op.create_index("ix_users_company", "users", ["company_id"])


def downgrade() -> None:
    op.drop_table("trend_clusters")
    op.drop_table("audit_logs")
    op.drop_table("notifications_config")
    op.drop_table("ticket_messages")
    op.drop_table("tickets")
    op.drop_table("knowledge_articles")
    op.drop_table("company_team_mappings")
    op.drop_table("users")
    op.drop_table("teams")
    op.drop_table("companies")
    # Drop enums
    for enum_name in ["user_role", "ticket_status", "ticket_priority", "ticket_source", "notification_event"]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
