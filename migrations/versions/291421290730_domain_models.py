"""domain models

Revision ID: 291421290730
Revises: 7317bd82e97f
Create Date: 2026-07-11 01:10:35.174264

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "291421290730"
down_revision: str | None = "7317bd82e97f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "inventory_items",
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("brand", sa.String(length=255), nullable=False),
        sa.Column("spec", sa.String(length=255), nullable=False),
        sa.Column("shape", sa.String(length=50), nullable=True),
        sa.Column("color", sa.String(length=50), nullable=True),
        sa.Column("sku", sa.String(length=50), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_inventory_items")),
    )
    op.create_index(
        op.f("ix_inventory_items_category"), "inventory_items", ["category"], unique=False
    )
    op.create_index(op.f("ix_inventory_items_sku"), "inventory_items", ["sku"], unique=True)
    op.create_table(
        "lens_coatings",
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
        sa.Column("name_en", sa.String(length=255), nullable=False),
        sa.Column("name_ar", sa.String(length=255), nullable=False),
        sa.Column("description_en", sa.String(length=500), nullable=False),
        sa.Column("description_ar", sa.String(length=500), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lens_coatings")),
    )
    op.create_table(
        "lens_materials",
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
        sa.Column("name_en", sa.String(length=255), nullable=False),
        sa.Column("name_ar", sa.String(length=255), nullable=False),
        sa.Column("description_en", sa.String(length=500), nullable=False),
        sa.Column("description_ar", sa.String(length=500), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lens_materials")),
    )
    op.create_table(
        "lens_tints",
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
        sa.Column("name_en", sa.String(length=255), nullable=False),
        sa.Column("name_ar", sa.String(length=255), nullable=False),
        sa.Column("description_en", sa.String(length=500), nullable=False),
        sa.Column("description_ar", sa.String(length=500), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lens_tints")),
    )
    op.create_table(
        "lens_types",
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
        sa.Column("name_en", sa.String(length=255), nullable=False),
        sa.Column("name_ar", sa.String(length=255), nullable=False),
        sa.Column("description_en", sa.String(length=500), nullable=False),
        sa.Column("description_ar", sa.String(length=500), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lens_types")),
    )
    op.create_table(
        "patients",
        sa.Column("name_en", sa.String(length=255), nullable=False),
        sa.Column("name_ar", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("town_en", sa.String(length=255), nullable=False),
        sa.Column("town_ar", sa.String(length=255), nullable=False),
        sa.Column("birth_year", sa.Integer(), nullable=False),
        sa.Column("last_visit", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("od_sph", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("od_cyl", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("od_axis", sa.Integer(), nullable=True),
        sa.Column("od_add", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("os_sph", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("os_cyl", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("os_axis", sa.Integer(), nullable=True),
        sa.Column("os_add", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("pd_dist", sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column("pd_near", sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column("diagnosis_en", sa.String(length=500), nullable=True),
        sa.Column("diagnosis_ar", sa.String(length=500), nullable=True),
        sa.Column("rx_number", sa.String(length=50), nullable=True),
        sa.Column("rx_date", sa.Date(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_patients")),
    )
    op.create_index(op.f("ix_patients_status"), "patients", ["status"], unique=False)
    op.create_table(
        "tips",
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("icon", sa.String(length=50), nullable=False),
        sa.Column("color", sa.String(length=50), nullable=False),
        sa.Column("title_en", sa.String(length=255), nullable=False),
        sa.Column("title_ar", sa.String(length=255), nullable=False),
        sa.Column("body_en", sa.String(length=1000), nullable=False),
        sa.Column("body_ar", sa.String(length=1000), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tips")),
    )
    op.create_index(op.f("ix_tips_category"), "tips", ["category"], unique=False)
    op.create_table(
        "lens_configs",
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("lens_type", sa.String(length=255), nullable=True),
        sa.Column("material", sa.String(length=255), nullable=True),
        sa.Column("coatings", sa.JSON(), nullable=False),
        sa.Column("tint", sa.String(length=255), nullable=True),
        sa.Column("frame_sku", sa.String(length=50), nullable=True),
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
            name=op.f("fk_lens_configs_patient_id_patients"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lens_configs")),
    )
    op.create_index(op.f("ix_lens_configs_patient_id"), "lens_configs", ["patient_id"], unique=True)
    op.create_table(
        "patient_notes",
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("en", sa.String(length=1000), nullable=False),
        sa.Column("ar", sa.String(length=1000), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name=op.f("fk_patient_notes_patient_id_patients"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_patient_notes")),
    )
    op.create_index(
        op.f("ix_patient_notes_patient_id"), "patient_notes", ["patient_id"], unique=False
    )
    op.create_table(
        "visit_history",
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("title_en", sa.String(length=255), nullable=False),
        sa.Column("title_ar", sa.String(length=255), nullable=False),
        sa.Column("detail_en", sa.String(length=1000), nullable=False),
        sa.Column("detail_ar", sa.String(length=1000), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name=op.f("fk_visit_history_patient_id_patients"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_visit_history")),
    )
    op.create_index(
        op.f("ix_visit_history_patient_id"), "visit_history", ["patient_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_visit_history_patient_id"), table_name="visit_history")
    op.drop_table("visit_history")
    op.drop_index(op.f("ix_patient_notes_patient_id"), table_name="patient_notes")
    op.drop_table("patient_notes")
    op.drop_index(op.f("ix_lens_configs_patient_id"), table_name="lens_configs")
    op.drop_table("lens_configs")
    op.drop_index(op.f("ix_tips_category"), table_name="tips")
    op.drop_table("tips")
    op.drop_index(op.f("ix_patients_status"), table_name="patients")
    op.drop_table("patients")
    op.drop_table("lens_types")
    op.drop_table("lens_tints")
    op.drop_table("lens_materials")
    op.drop_table("lens_coatings")
    op.drop_index(op.f("ix_inventory_items_sku"), table_name="inventory_items")
    op.drop_index(op.f("ix_inventory_items_category"), table_name="inventory_items")
    op.drop_table("inventory_items")
