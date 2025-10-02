"""seed mock data

Revision ID: 43443c1e0b58
Revises: b6652809e7bc
Create Date: 2025-10-03 00:15:00
"""
from alembic import op

revision = "43443c1e0b58"
down_revision = "b6652809e7bc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # пользователи — БД сама поставит registered_at и is_verified по дефолту
    op.execute(
        """
        INSERT INTO users (name, email, avatar_url)
        VALUES
          ('Alice', 'alice@example.com', NULL),
          ('Bob',   'bob@example.com',   NULL),
          ('Eve',   'eve@example.com',   NULL)
        ON CONFLICT (email) DO NOTHING;
        """
    )

    # новости — content без ::jsonb (столбец JSON), published_at поставит дефолт
    op.execute(
        """
        INSERT INTO news (title, content, cover_url, author_id)
        SELECT
          'Alice first post',
          '{"blocks":["seed post 1"]}',
          NULL,
          u.id
        FROM users u
        WHERE u.email = 'alice@example.com'
        ON CONFLICT DO NOTHING;
        """
    )
    op.execute(
        """
        INSERT INTO news (title, content, cover_url, author_id)
        SELECT
          'Bob''s update',
          '{"blocks":["seed post 2"]}',
          NULL,
          u.id
        FROM users u
        WHERE u.email = 'bob@example.com'
        ON CONFLICT DO NOTHING;
        """
    )

    # комментарии — поле текста называется text, published_at поставит дефолт
    op.execute(
        """
        INSERT INTO comments (news_id, author_id, text)
        SELECT n.id, u.id, 'seed comment 1'
        FROM news n
        JOIN users u ON u.email = 'eve@example.com'
        WHERE n.title = 'Alice first post'
        LIMIT 1;
        """
    )
    op.execute(
        """
        INSERT INTO comments (news_id, author_id, text)
        SELECT n.id, u.id, 'seed comment 2'
        FROM news n
        JOIN users u ON u.email = 'alice@example.com'
        WHERE n.title = 'Bob''s update'
        LIMIT 1;
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM comments WHERE text IN ('seed comment 1','seed comment 2');")
    op.execute("DELETE FROM news WHERE title IN ('Alice first post','Bob''s update');")
    op.execute("DELETE FROM users WHERE email IN ('alice@example.com','bob@example.com','eve@example.com');")
