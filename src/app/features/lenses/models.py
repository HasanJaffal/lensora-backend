import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantEntity, TenantMixin, UuidPrimaryKeyMixin


class LensOptionMixin:
    """Shared columns for every lens catalog (type, material, coating, tint).

    ``price`` is the price delta added to the order total; a value of 0 means the
    option is included at no extra cost (e.g. the standard 1.50 material).
    """

    name_en: Mapped[str] = mapped_column(String(255))
    name_ar: Mapped[str] = mapped_column(String(255))
    description_en: Mapped[str] = mapped_column(String(500))
    description_ar: Mapped[str] = mapped_column(String(500))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))


class LensType(TenantEntity, LensOptionMixin):
    __tablename__ = "lens_types"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "name_en", name="uq_lens_types_organization_id_name_en"
        ),
    )


class LensMaterial(TenantEntity, LensOptionMixin):
    __tablename__ = "lens_materials"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "name_en", name="uq_lens_materials_organization_id_name_en"
        ),
    )


class LensCoating(TenantEntity, LensOptionMixin):
    __tablename__ = "lens_coatings"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "name_en", name="uq_lens_coatings_organization_id_name_en"
        ),
    )


class LensTint(TenantEntity, LensOptionMixin):
    __tablename__ = "lens_tints"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "name_en", name="uq_lens_tints_organization_id_name_en"
        ),
    )


class Order(TenantEntity):
    """A confirmed lens order: a priced snapshot of the configurator selections.

    Prices and labels are denormalized so the order survives later catalog or stock
    edits — it records what was ordered and charged at confirmation time.
    """

    __tablename__ = "orders"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    deposit: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    deposit_percent: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    frame_sku: Mapped[str | None] = mapped_column(String(50), default=None)
    frame_name: Mapped[str | None] = mapped_column(String(255), default=None)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItem.position",
    )


class OrderItem(Base, UuidPrimaryKeyMixin, TenantMixin):
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    label_en: Mapped[str] = mapped_column(String(255))
    label_ar: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped["Order"] = relationship(back_populates="items")
