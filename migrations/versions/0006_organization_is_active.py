"""organization is_active

Revision ID: 3d7a1c04b8e2
Revises: 1f6c8f2e9a3b
Create Date: 2026-07-25 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3d7a1c04b8e2"
down_revision: str | None = "1f6c8f2e9a3b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # server_default backfills existing rows as active; dropped afterwards so the
    # application default is the single source of truth for new rows.
    op.add_column(
        "organization",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("organization", "is_active", server_default=None)


def downgrade() -> None:
    op.drop_column("organization", "is_active")
