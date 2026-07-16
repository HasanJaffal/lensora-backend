from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin


class InventoryCategory(StrEnum):
    FRAME = "frame"
    SUN = "sun"
    LENS = "lens"
    CONTACT = "contact"
    SOLUTION = "solution"
    CARE = "care"


class InventoryItem(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "inventory_items"

    category: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str] = mapped_column(String(255))
    spec: Mapped[str] = mapped_column(String(255))
    shape: Mapped[str | None] = mapped_column(String(50), default=None)
    color: Mapped[str | None] = mapped_column(String(50), default=None)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    threshold: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
