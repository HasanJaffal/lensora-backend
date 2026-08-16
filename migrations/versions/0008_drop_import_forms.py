"""drop import_forms

Revision ID: 9c4d0e6a2b71
Revises: 6b2e9f5c71da
Create Date: 2026-08-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9c4d0e6a2b71"
down_revision: str | None = "6b2e9f5c71da"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(op.f("ix_import_forms_organization_id"), table_name="import_forms")
    op.drop_table("import_forms")


def downgrade() -> None:
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
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["user_account.id"],
            name=op.f("fk_import_forms_created_by_user_account"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_import_forms_organization_id_organization"),
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["user_account.id"],
            name=op.f("fk_import_forms_updated_by_user_account"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_forms")),
    )
    op.create_index(
        op.f("ix_import_forms_organization_id"), "import_forms", ["organization_id"], unique=False
    )
