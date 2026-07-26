import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import (
    AttachmentNotFoundError,
    AttachmentTooLargeError,
    AttachmentUnsupportedTypeError,
    TenantContextMissingError,
)
from app.common.tenant_context import TenantContext
from app.features.attachments.models import Attachment
from app.features.attachments.repository import AttachmentRepository
from app.features.attachments.schemas import (
    AttachmentDto,
    SignedUrlDto,
    UploadAuthorizationDto,
    UploadAuthorizationRequest,
)
from app.storage.client import ObjectStorage
from app.storage.folders import AttachmentFolder
from app.storage.paths import build_storage_path, is_within_organization

MAX_ATTACHMENT_SIZE_BYTES = 25 * 1024 * 1024

_ALLOWED_CONTENT_TYPES = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)


class AttachmentService:
    """Upload authorization, retrieval, and deletion of tenant-owned attachments.

    The organization folder is always taken from the bound ``TenantContext`` and never from the
    request, so an authenticated caller can only ever read or write inside its own prefix.
    """

    def __init__(
        self,
        session: AsyncSession,
        tenant_context: TenantContext,
        storage: ObjectStorage,
        signed_url_expires_seconds: int,
    ) -> None:
        self._repository = AttachmentRepository(session, tenant_context)
        self._tenant_context = tenant_context
        self._storage = storage
        self._signed_url_expires_seconds = signed_url_expires_seconds

    async def authorize_upload(
        self, request: UploadAuthorizationRequest
    ) -> UploadAuthorizationDto:
        if request.content_type not in _ALLOWED_CONTENT_TYPES:
            raise AttachmentUnsupportedTypeError(
                f"Unsupported file type '{request.content_type}'; expected PDF, JPEG, PNG, or WebP"
            )
        if request.size_bytes > MAX_ATTACHMENT_SIZE_BYTES:
            raise AttachmentTooLargeError("File exceeds the 25 MB limit")

        storage_path = build_storage_path(
            organization_id=self._tenant_context.organization_id,
            folder=request.subfolder,
            original_file_name=request.original_file_name,
        )
        signed_upload = await self._storage.create_signed_upload(
            str(storage_path), allow_overwrite=False
        )

        attachment = Attachment(
            storage_path=str(storage_path),
            original_file_name=request.original_file_name,
            content_type=request.content_type,
            size_bytes=request.size_bytes,
            subfolder=request.subfolder.value,
            is_uploaded=False,
        )
        self._repository.add(attachment)
        await self._repository.commit()
        await self._repository.refresh(attachment)

        return UploadAuthorizationDto(
            attachment=AttachmentDto.from_model(attachment),
            upload_url=signed_upload.upload_url,
        )

    async def confirm_upload(self, attachment_id: uuid.UUID) -> AttachmentDto:
        attachment = await self._require_attachment(attachment_id)
        attachment.is_uploaded = True
        await self._repository.commit()
        await self._repository.refresh(attachment)
        return AttachmentDto.from_model(attachment)

    async def list_attachments(self, subfolder: AttachmentFolder) -> list[AttachmentDto]:
        attachments = await self._repository.list_by_subfolder(subfolder.value)
        return [AttachmentDto.from_model(attachment) for attachment in attachments]

    async def create_signed_url(self, attachment_id: uuid.UUID) -> SignedUrlDto:
        attachment = await self._require_attachment(attachment_id)
        url = await self._storage.create_signed_download_url(
            attachment.storage_path, expires_in=self._signed_url_expires_seconds
        )
        return SignedUrlDto(url=url, expires_in=self._signed_url_expires_seconds)

    async def delete_attachment(self, attachment_id: uuid.UUID) -> None:
        """Remove the stored object first, then its metadata row.

        Ordering matters: if the storage delete fails the row survives and the caller can retry,
        whereas dropping the row first would orphan the object with no way to reach it.
        """
        attachment = await self._require_attachment(attachment_id)
        await self._storage.delete(attachment.storage_path)
        await self._repository.delete(attachment)
        await self._repository.commit()

    async def _require_attachment(self, attachment_id: uuid.UUID) -> Attachment:
        attachment = await self._repository.get_by_id(attachment_id)
        if attachment is None:
            raise AttachmentNotFoundError(f"Attachment {attachment_id} not found")
        if not is_within_organization(
            attachment.storage_path, self._tenant_context.organization_id
        ):
            raise TenantContextMissingError(
                f"Attachment {attachment_id} resolves outside its organization's storage prefix"
            )
        return attachment
