import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantEntity


class IntakeStatus(StrEnum):
    DRAFT = "draft"
    COMPLETED = "completed"


class IntakeSubmission(TenantEntity):
    """A first-visit intake questionnaire (FR-INT).

    Each BRD section is persisted as a structured JSON document so the form can evolve
    without a migration per field. Completing an intake opens the patient record it stands for,
    and ``patient_id`` links the questionnaire to that record; a draft has none yet.
    """

    __tablename__ = "intake_submissions"

    status: Mapped[str] = mapped_column(default=IntakeStatus.DRAFT, index=True)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("patients.id", ondelete="SET NULL"), default=None, index=True
    )
    individual_info: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    motive: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    themes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    refraction_history: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    antecedents: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
