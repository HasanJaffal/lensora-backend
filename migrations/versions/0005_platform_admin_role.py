"""platform admin role

Revision ID: 1f6c8f2e9a3b
Revises: 85042019be58
Create Date: 2026-07-18 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1f6c8f2e9a3b"
down_revision: str | None = "85042019be58"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(op.f("ix_user_account_organization_id"), table_name="user_account")
    op.alter_column("user_account", "organization_id", existing_type=sa.Uuid(), nullable=True)
    op.create_index(
        op.f("ix_user_account_organization_id"), "user_account", ["organization_id"]
    )
    op.create_unique_constraint(
        op.f("uq_user_account_organization_id"), "user_account", ["organization_id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("uq_user_account_organization_id"), "user_account", type_="unique"
    )
    op.drop_index(op.f("ix_user_account_organization_id"), table_name="user_account")
    op.alter_column("user_account", "organization_id", existing_type=sa.Uuid(), nullable=False)
    op.create_index(
        op.f("ix_user_account_organization_id"), "user_account", ["organization_id"], unique=True
    )
