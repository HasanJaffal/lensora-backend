import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin


class PatientStatus(StrEnum):
    LAB = "lab"
    READY = "ready"
    ACTIVE = "active"


class Patient(Base, UuidPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "patients"

    name_en: Mapped[str] = mapped_column(String(255))
    name_ar: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(50))
    town_en: Mapped[str] = mapped_column(String(255))
    town_ar: Mapped[str] = mapped_column(String(255))
    birth_year: Mapped[int] = mapped_column(Integer)
    last_visit: Mapped[date | None] = mapped_column(Date, default=None)
    status: Mapped[str] = mapped_column(String(20), index=True)

    od_sph: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), default=None)
    od_cyl: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), default=None)
    od_axis: Mapped[int | None] = mapped_column(Integer, default=None)
    od_add: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), default=None)
    os_sph: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), default=None)
    os_cyl: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), default=None)
    os_axis: Mapped[int | None] = mapped_column(Integer, default=None)
    os_add: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), default=None)
    pd_dist: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), default=None)
    pd_near: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), default=None)

    diagnosis_en: Mapped[str | None] = mapped_column(String(500), default=None)
    diagnosis_ar: Mapped[str | None] = mapped_column(String(500), default=None)

    rx_number: Mapped[str | None] = mapped_column(String(50), default=None)
    rx_date: Mapped[date | None] = mapped_column(Date, default=None)

    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    notes: Mapped[list["PatientNote"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="PatientNote.created_at.desc()",
    )
    visits: Mapped[list["VisitHistory"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="VisitHistory.date.desc()",
    )
    lens_config: Mapped["LensConfig | None"] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        uselist=False,
    )


class PatientNote(Base, UuidPrimaryKeyMixin):
    __tablename__ = "patient_notes"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    en: Mapped[str] = mapped_column(String(1000))
    ar: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    patient: Mapped["Patient"] = relationship(back_populates="notes")


class VisitHistory(Base, UuidPrimaryKeyMixin):
    __tablename__ = "visit_history"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[date] = mapped_column(Date)
    title_en: Mapped[str] = mapped_column(String(255))
    title_ar: Mapped[str] = mapped_column(String(255))
    detail_en: Mapped[str] = mapped_column(String(1000))
    detail_ar: Mapped[str] = mapped_column(String(1000))

    patient: Mapped["Patient"] = relationship(back_populates="visits")


class LensConfig(Base, UuidPrimaryKeyMixin, TimestampMixin):
    """The patient's current lens configuration snapshot.

    Stores catalog references by name rather than foreign keys so the record survives
    catalog edits and mirrors the denormalized snapshot an order captures.
    """

    __tablename__ = "lens_configs"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), unique=True, index=True
    )
    lens_type: Mapped[str | None] = mapped_column(String(255), default=None)
    material: Mapped[str | None] = mapped_column(String(255), default=None)
    coatings: Mapped[list[str]] = mapped_column(JSON, default=list)
    tint: Mapped[str | None] = mapped_column(String(255), default=None)
    frame_sku: Mapped[str | None] = mapped_column(String(50), default=None)

    patient: Mapped["Patient"] = relationship(back_populates="lens_config")
