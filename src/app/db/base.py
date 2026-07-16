import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UuidPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TenantMixin:
    """Adds the tenant-ownership column. Applied to models scoped to an organization."""

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organization.id"), index=True)


class AuditMixin:
    """Adds actor-tracking columns, auto-populated by the listeners in ``app.db.audit``.

    Nullable because CLI/seed/system inserts run with no authenticated actor bound.
    """

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user_account.id"), default=None
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("user_account.id"), default=None
    )


class Entity(Base, UuidPrimaryKeyMixin, TimestampMixin, AuditMixin):
    """Convenience base for global models: Uuid + Timestamp + Audit."""

    __abstract__ = True


class TenantEntity(Base, UuidPrimaryKeyMixin, TimestampMixin, AuditMixin, TenantMixin):
    """Convenience base for tenant-owned models: Uuid + Timestamp + Audit + Tenant."""

    __abstract__ = True
