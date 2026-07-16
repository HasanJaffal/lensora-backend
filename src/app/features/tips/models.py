from enum import StrEnum

from sqlalchemy import JSON, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantEntity


class TipCategory(StrEnum):
    SCREEN = "screen"
    LENS_CARE = "lensCare"
    ADAPTING = "adapting"
    CHILDREN = "children"
    SUN_UV = "sunUv"


class Tip(TenantEntity):
    __tablename__ = "tips"
    __table_args__ = (
        UniqueConstraint("organization_id", "title_en", name="uq_tips_organization_id_title_en"),
        Index("ix_tips_organization_id_category", "organization_id", "category"),
    )

    category: Mapped[str] = mapped_column(String(20))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    icon: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(50))
    title_en: Mapped[str] = mapped_column(String(255))
    title_ar: Mapped[str] = mapped_column(String(255))
    body_en: Mapped[str] = mapped_column(String(1000))
    body_ar: Mapped[str] = mapped_column(String(1000))
