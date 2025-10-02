"""create users/news/comments

Revision ID: b6652809e7bc
Revises: <base>
Create Date: 2025-10-02 23:39:26.619333
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b6652809e7bc"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----- users -----
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column(
            "registered_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "is_verified",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ----- news -----
    op.create_table(
        "news",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("content", sa.JSON(), nullable=True),  # соответствует ORM (JSON)
        sa.Column(
            "published_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("cover_url", sa.String(length=500), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_news_author_id", "news", ["author_id"], unique=False)

    # ----- comments -----
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "published_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("news_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["news_id"], ["news.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_comments_news_id", "comments", ["news_id"], unique=False)
    op.create_index("ix_comments_author_id", "comments", ["author_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_comments_author_id", table_name="comments")
    op.drop_index("ix_comments_news_id", table_name="comments")
    op.drop_table("comments")

    op.drop_index("ix_news_author_id", table_name="news")
    op.drop_table("news")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
