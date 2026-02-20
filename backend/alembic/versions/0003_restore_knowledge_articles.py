"""Restore knowledge_articles table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create knowledge_articles table."""
    op.create_table(
        "knowledge_articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=True),
        sa.Column("view_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Create indexes for better query performance
    op.create_index("ix_knowledge_articles_company_id", "knowledge_articles", ["company_id"])
    op.create_index("ix_knowledge_articles_category", "knowledge_articles", ["category"])


def downgrade() -> None:
    """Drop knowledge_articles table."""
    op.drop_index("ix_knowledge_articles_category", "knowledge_articles")
    op.drop_index("ix_knowledge_articles_company_id", "knowledge_articles")
    op.drop_table("knowledge_articles")
