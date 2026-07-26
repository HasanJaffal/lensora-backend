from datetime import datetime

from pydantic import Field

from app.common.schema import CamelModel
from app.features.attachments.models import Attachment
from app.storage.folders import AttachmentFolder


class AttachmentDto(CamelModel):
    id: str
    subfolder: str
    storage_path: str
    original_file_name: str
    content_type: str
    size_bytes: int
    is_uploaded: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, attachment: Attachment) -> "AttachmentDto":
        return cls(
            id=str(attachment.id),
            subfolder=attachment.subfolder,
            storage_path=attachment.storage_path,
            original_file_name=attachment.original_file_name,
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            is_uploaded=attachment.is_uploaded,
            created_at=attachment.created_at,
            updated_at=attachment.updated_at,
        )


class UploadAuthorizationRequest(CamelModel):
    """Client-supplied intent for a new upload.

    ``subfolder`` is an enum rather than a free string: the storage path is composed on the
    server, so a client can never choose an arbitrary location.
    """

    subfolder: AttachmentFolder
    original_file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=150)
    size_bytes: int = Field(ge=0)


class UploadAuthorizationDto(CamelModel):
    """The signed URL the browser PUTs to, plus the pending metadata row it belongs to."""

    attachment: AttachmentDto
    upload_url: str


class SignedUrlDto(CamelModel):
    url: str
    expires_in: int
