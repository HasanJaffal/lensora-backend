from enum import StrEnum

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin


class TipCategory(StrEnum):
    SCREEN = "screen"
    LENS_CARE = "lensCare"
    ADAPTING = "adapting"
    CHILDREN = "children"
    SUN_UV = "sunUv"


class Tip(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tips"

    category: Mapped[str] = mapped_column(String(20), index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    icon: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(50))
    title_en: Mapped[str] = mapped_column(String(255))
    title_ar: Mapped[str] = mapped_column(String(255))
    body_en: Mapped[str] = mapped_column(String(1000))
    body_ar: Mapped[str] = mapped_column(String(1000))
