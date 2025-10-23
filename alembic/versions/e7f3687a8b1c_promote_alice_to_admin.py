"""promote alice to admin

Revision ID: e7f3687a8b1c
Revises: 035034072d9f
Create Date: 2025-10-23 20:58:47.930340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f3687a8b1c'
down_revision: Union[str, Sequence[str], None] = '035034072d9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE users SET is_admin = true WHERE email = 'alice@example.com';")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE users SET is_admin = false WHERE email = 'alice@example.com';")

