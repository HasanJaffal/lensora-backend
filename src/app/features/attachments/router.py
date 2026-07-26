import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.common.deps import SessionDep, TenantContextDep, require_auth
from app.common.envelope import Envelope, ok
from app.core.config import get_settings
from app.features.attachments.schemas import (
    AttachmentDto,
    SignedUrlDto,
    UploadAuthorizationDto,
    UploadAuthorizationRequest,
)
from app.features.attachments.service import AttachmentService
from app.storage.deps import get_object_storage
from app.storage.folders import AttachmentFolder

router = APIRouter(
    prefix="/attachments", tags=["attachments"], dependencies=[Depends(require_auth)]
)


def get_attachment_service(
    session: SessionDep, tenant_context: TenantContextDep
) -> AttachmentService:
    return AttachmentService(
        session,
        tenant_context,
        get_object_storage(),
        get_settings().attachment_signed_url_expires_seconds,
    )


AttachmentServiceDep = Annotated[AttachmentService, Depends(get_attachment_service)]


@router.post("/upload-authorizations")
async def authorize_upload(
    request: UploadAuthorizationRequest, service: AttachmentServiceDep
) -> Envelope[UploadAuthorizationDto]:
    return ok(await service.authorize_upload(request))


@router.get("")
async def list_attachments(
    service: AttachmentServiceDep,
    subfolder: Annotated[AttachmentFolder, Query()],
) -> Envelope[list[AttachmentDto]]:
    return ok(await service.list_attachments(subfolder))


@router.post("/{attachment_id}/confirm")
async def confirm_upload(
    attachment_id: uuid.UUID, service: AttachmentServiceDep
) -> Envelope[AttachmentDto]:
    return ok(await service.confirm_upload(attachment_id))


@router.get("/{attachment_id}/signed-url")
async def get_signed_url(
    attachment_id: uuid.UUID, service: AttachmentServiceDep
) -> Envelope[SignedUrlDto]:
    return ok(await service.create_signed_url(attachment_id))


@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: uuid.UUID, service: AttachmentServiceDep
) -> Envelope[None]:
    await service.delete_attachment(attachment_id)
    return ok(None)
