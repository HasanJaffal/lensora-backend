from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Entity


class Organization(Entity):
    __tablename__ = "organization"

    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    deposit_percent: Mapped[Decimal] = mapped_column(Numeric(precision=5, scale=4))
