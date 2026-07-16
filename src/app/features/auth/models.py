import uuid
from enum import StrEnum

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin


class UserRole(StrEnum):
    ORGANIZATION_ADMIN = "organizationAdmin"


class User(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_account"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization.id"), unique=True, index=True
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    display_name_en: Mapped[str] = mapped_column(String(255))
    display_name_ar: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default=UserRole.ORGANIZATION_ADMIN)
    is_active: Mapped[bool] = mapped_column(default=True)
