"""Add Google OAuth fields to users

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-21
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_email", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("google_access_token", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("google_refresh_token", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("google_token_scope", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("google_token_expiry", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("google_connected_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "google_connected_at")
    op.drop_column("users", "google_token_expiry")
    op.drop_column("users", "google_token_scope")
    op.drop_column("users", "google_refresh_token")
    op.drop_column("users", "google_access_token")
    op.drop_column("users", "google_email")
