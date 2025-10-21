"""add auth fields and refresh_sessions

Revision ID: 035034072d9f
Revises: 43443c1e0b58
Create Date: 2025-10-16 21:35:07.384877

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '035034072d9f'
down_revision: Union[str, Sequence[str], None] = '43443c1e0b58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("is_verified_author", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("password_hash", sa.String(length=256), nullable=True))
    op.add_column("users", sa.Column("github_id", sa.String(length=64), nullable=True))
    op.create_unique_constraint("uq_users_github_id", "users", ["github_id"])

    op.drop_column("users", "is_verified")

    op.alter_column("users", "is_admin", server_default=None)
    op.alter_column("users", "is_verified_author", server_default=None)

    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token", sa.String(length=500), nullable=False, unique=True),
        sa.Column("user_agent", sa.String(length=400), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"], unique=False)
    op.create_index("ix_refresh_sessions_revoked", "refresh_sessions", ["revoked"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_refresh_sessions_revoked", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_user_id", table_name="refresh_sessions")
    op.drop_table("refresh_sessions")

    op.drop_constraint("uq_users_github_id", "users", type_="unique")
    op.drop_column("users", "github_id")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "is_verified_author")
    op.drop_column("users", "is_admin")

    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.alter_column("users", "is_verified", server_default=None)

