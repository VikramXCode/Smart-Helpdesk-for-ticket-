"""Add AI response fields to tickets table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-20
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add AI response fields to tickets table."""
    # Add ai_response field (stores the AI-generated English response)
    op.add_column(
        "tickets",
        sa.Column("ai_response", sa.Text, nullable=True)
    )

    # Add ai_confidence field (confidence score from AI model)
    op.add_column(
        "tickets",
        sa.Column("ai_confidence", sa.Float, nullable=True)
    )

    # Add ai_predicted_category field (AI's category prediction)
    op.add_column(
        "tickets",
        sa.Column("ai_predicted_category", sa.String(100), nullable=True)
    )

    # Add ai_suggested_priority field (AI's priority suggestion)
    op.add_column(
        "tickets",
        sa.Column("ai_suggested_priority", sa.String(20), nullable=True)
    )

    # Add is_ai_duplicate field (duplicate detection flag)
    op.add_column(
        "tickets",
        sa.Column("is_ai_duplicate", sa.Boolean, nullable=True)
    )


def downgrade() -> None:
    """Remove AI response fields from tickets table."""
    op.drop_column("tickets", "is_ai_duplicate")
    op.drop_column("tickets", "ai_suggested_priority")
    op.drop_column("tickets", "ai_predicted_category")
    op.drop_column("tickets", "ai_confidence")
    op.drop_column("tickets", "ai_response")
