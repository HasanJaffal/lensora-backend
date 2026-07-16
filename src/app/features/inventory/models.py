from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantEntity


class InventoryCategory(StrEnum):
    FRAME = "frame"
    SUN = "sun"
    LENS = "lens"
    CONTACT = "contact"
    SOLUTION = "solution"
    CARE = "care"


class InventoryItem(TenantEntity):
    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_inventory_items_organization_id_sku"),
        Index("ix_inventory_items_organization_id_category", "organization_id", "category"),
    )

    category: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str] = mapped_column(String(255))
    spec: Mapped[str] = mapped_column(String(255))
    shape: Mapped[str | None] = mapped_column(String(50), default=None)
    color: Mapped[str | None] = mapped_column(String(50), default=None)
    sku: Mapped[str] = mapped_column(String(50))
    quantity: Mapped[int] = mapped_column(Integer)
    threshold: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
