"""intake submissions

Revision ID: c7f2a9d413ab
Revises: b4e1c2a37d90
Create Date: 2026-07-13 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c7f2a9d413ab"
down_revision: str | None = "b4e1c2a37d90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "intake_submissions",
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=True),
        sa.Column("individual_info", sa.JSON(), nullable=False),
        sa.Column("motive", sa.JSON(), nullable=False),
        sa.Column("themes", sa.JSON(), nullable=False),
        sa.Column("refraction_history", sa.JSON(), nullable=False),
        sa.Column("antecedents", sa.JSON(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name=op.f("fk_intake_submissions_patient_id_patients"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_intake_submissions")),
    )
    op.create_index(
        op.f("ix_intake_submissions_patient_id"),
        "intake_submissions",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_intake_submissions_status"),
        "intake_submissions",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_intake_submissions_status"), table_name="intake_submissions"
    )
    op.drop_index(
        op.f("ix_intake_submissions_patient_id"), table_name="intake_submissions"
    )
    op.drop_table("intake_submissions")
