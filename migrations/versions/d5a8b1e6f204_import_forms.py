"""import forms

Revision ID: d5a8b1e6f204
Revises: c7f2a9d413ab
Create Date: 2026-07-13 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d5a8b1e6f204"
down_revision: str | None = "c7f2a9d413ab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "import_forms",
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("source_file_name", sa.String(length=255), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("used_fallback", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_forms")),
    )


def downgrade() -> None:
    op.drop_table("import_forms")
