from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin


class ImportStatus(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ImportForm(Base, UuidPrimaryKeyMixin, TimestampMixin):
    """Result of extracting questions from an uploaded paper form (FR-IMP).

    Only the extracted questions are persisted — never the uploaded document itself
    (NFR-5); the file is processed in-session and discarded.
    """

    __tablename__ = "import_forms"

    status: Mapped[str] = mapped_column(String(20), default=ImportStatus.PROCESSING)
    source_file_name: Mapped[str] = mapped_column(String(255))
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    used_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
