"""timezone aware timestamps

Revision ID: 3e56a74fcc48
Revises: d5ad2dc886e2
Create Date: 2026-06-06 19:00:43.795134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '3e56a74fcc48'
down_revision: Union[str, None] = 'd5ad2dc886e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMPTZ")
    op.execute("ALTER TABLE users ALTER COLUMN updated_at TYPE TIMESTAMPTZ")
    op.execute("ALTER TABLE conversations ALTER COLUMN created_at TYPE TIMESTAMPTZ")
    op.execute("ALTER TABLE conversations ALTER COLUMN updated_at TYPE TIMESTAMPTZ")
    op.execute("ALTER TABLE messages ALTER COLUMN created_at TYPE TIMESTAMPTZ")

def downgrade() -> None:
    pass