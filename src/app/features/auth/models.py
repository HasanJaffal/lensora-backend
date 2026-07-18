import uuid
from enum import StrEnum

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Entity


class UserRole(StrEnum):
    ORGANIZATION_ADMIN = "organizationAdmin"
    PLATFORM_ADMIN = "platformAdmin"


class User(Entity):
    __tablename__ = "user_account"
    __table_args__ = (
        # Postgres treats NULLs as distinct for uniqueness, so this allows unlimited
        # PLATFORM_ADMIN rows (organization_id is NULL) while still enforcing one
        # ORGANIZATION_ADMIN per organization.
        UniqueConstraint("organization_id", name="uq_user_account_organization_id"),
    )

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organization.id"), index=True
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    display_name_en: Mapped[str] = mapped_column(String(255))
    display_name_ar: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default=UserRole.ORGANIZATION_ADMIN)
    is_active: Mapped[bool] = mapped_column(default=True)
