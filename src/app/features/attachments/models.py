from sqlalchemy import BigInteger, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantEntity


class Attachment(TenantEntity):
    """Metadata for one object in the storage bucket.

    The bytes live in Supabase Storage under ``{organization_id}/{subfolder}/{file}``; this row
    is the tenant-owned record of them and the only way the application resolves a path.
    """

    __tablename__ = "attachments"
    __table_args__ = (
        UniqueConstraint("storage_path", name="uq_attachments_storage_path"),
        Index("ix_attachments_organization_id_subfolder", "organization_id", "subfolder"),
    )

    storage_path: Mapped[str] = mapped_column(String(500))
    original_file_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(150))
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    subfolder: Mapped[str] = mapped_column(String(50))
    is_uploaded: Mapped[bool] = mapped_column(default=False)
