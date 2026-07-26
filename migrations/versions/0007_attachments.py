"""attachments

Revision ID: 6b2e9f5c71da
Revises: 3d7a1c04b8e2
Create Date: 2026-07-26 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6b2e9f5c71da"
down_revision: str | None = "3d7a1c04b8e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attachments",
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("original_file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=150), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("subfolder", sa.String(length=50), nullable=False),
        sa.Column("is_uploaded", sa.Boolean(), nullable=False),
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
            name=op.f("fk_attachments_created_by_user_account"),
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_attachments_organization_id_organization"),
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["user_account.id"],
            name=op.f("fk_attachments_updated_by_user_account"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attachments")),
        sa.UniqueConstraint("storage_path", name="uq_attachments_storage_path"),
    )
    op.create_index(
        op.f("ix_attachments_organization_id"), "attachments", ["organization_id"], unique=False
    )
    op.create_index(
        "ix_attachments_organization_id_subfolder",
        "attachments",
        ["organization_id", "subfolder"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_attachments_organization_id_subfolder", table_name="attachments")
    op.drop_index(op.f("ix_attachments_organization_id"), table_name="attachments")
    op.drop_table("attachments")
