import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.common.deps import SessionDep, TenantContextDep, require_auth
from app.common.envelope import Envelope, ok
from app.features.ai.deps import get_ai_provider, get_fallback_provider
from app.features.import_forms.schemas import ImportDto, IntakeFormDefinitionDto
from app.features.import_forms.service import ImportService

router = APIRouter(prefix="/imports", tags=["imports"], dependencies=[Depends(require_auth)])


def get_import_service(session: SessionDep, tenant_context: TenantContextDep) -> ImportService:
    return ImportService(session, tenant_context, get_ai_provider(), get_fallback_provider())


ImportServiceDep = Annotated[ImportService, Depends(get_import_service)]


@router.post("")
async def create_import(
    service: ImportServiceDep,
    file: Annotated[UploadFile, File()],
) -> Envelope[ImportDto]:
    data = await file.read()
    return ok(
        await service.create_import(
            filename=file.filename or "upload",
            content_type=file.content_type or "application/octet-stream",
            data=data,
        )
    )


@router.get("/{import_id}")
async def get_import(import_id: uuid.UUID, service: ImportServiceDep) -> Envelope[ImportDto]:
    return ok(await service.get_import(import_id))


@router.post("/{import_id}/use-as-intake")
async def use_as_intake(
    import_id: uuid.UUID, service: ImportServiceDep
) -> Envelope[IntakeFormDefinitionDto]:
    return ok(await service.use_as_intake(import_id))
