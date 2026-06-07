"""add memory status and sensitivity fields

Revision ID: 53a34c53264e
Revises: d5ad2dc886e2
Create Date: 2026-06-07 16:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "53a34c53264e"
down_revision: Union[str, None] = "d5ad2dc886e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


memory_status = sa.Enum("active", "latent", "user_reopened", name="memorystatus")


def upgrade() -> None:
    bind = op.get_bind()
    memory_status.create(bind, checkfirst=True)

    op.add_column(
        "user_memories",
        sa.Column("status", memory_status, nullable=False, server_default="active"),
    )
    op.add_column(
        "user_memories",
        sa.Column("sensitivity_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "user_memories",
        sa.Column("sessions_since_surfaced", sa.Integer(), nullable=False, server_default="0"),
    )
    op.drop_column("user_memories", "is_active")


def downgrade() -> None:
    bind = op.get_bind()

    op.add_column(
        "user_memories",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.drop_column("user_memories", "sessions_since_surfaced")
    op.drop_column("user_memories", "sensitivity_flag")
    op.drop_column("user_memories", "status")

    memory_status.drop(bind, checkfirst=True)
