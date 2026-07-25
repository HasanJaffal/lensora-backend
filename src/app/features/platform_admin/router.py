import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.common.deps import SessionDep, require_platform_admin
from app.common.envelope import Envelope, Meta, ok
from app.common.pagination import PageParams
from app.features.auth.repository import UserRepository
from app.features.organizations.repository import OrganizationRepository
from app.features.platform_admin.schemas import (
    CreateOrganizationRequest,
    OrganizationDto,
    PlatformAdminDashboardDto,
    SetOrganizationStatusRequest,
)
from app.features.platform_admin.service import PlatformAdminService

router = APIRouter(
    prefix="/platform-admin",
    tags=["platform-admin"],
    dependencies=[Depends(require_platform_admin)],
)


def get_platform_admin_service(session: SessionDep) -> PlatformAdminService:
    return PlatformAdminService(session, OrganizationRepository(session), UserRepository(session))


PlatformAdminServiceDep = Annotated[PlatformAdminService, Depends(get_platform_admin_service)]


@router.get("/organizations")
async def list_organizations(
    service: PlatformAdminServiceDep,
    page_params: Annotated[PageParams, Depends()],
) -> Envelope[list[OrganizationDto]]:
    items, pagination = await service.list_organizations(
        page=page_params.page, page_size=page_params.page_size, offset=page_params.offset
    )
    return ok(items, meta=Meta(pagination=pagination))


@router.post("/organizations")
async def create_organization(
    body: CreateOrganizationRequest, service: PlatformAdminServiceDep
) -> Envelope[OrganizationDto]:
    return ok(await service.create_organization(body))


@router.get("/organizations/{organization_id}")
async def get_organization(
    organization_id: uuid.UUID, service: PlatformAdminServiceDep
) -> Envelope[OrganizationDto]:
    return ok(await service.get_organization(organization_id))


@router.patch("/organizations/{organization_id}/status")
async def set_organization_status(
    organization_id: uuid.UUID,
    body: SetOrganizationStatusRequest,
    service: PlatformAdminServiceDep,
) -> Envelope[OrganizationDto]:
    return ok(await service.set_organization_status(organization_id, is_active=body.is_active))


@router.get("/dashboard")
async def get_dashboard(service: PlatformAdminServiceDep) -> Envelope[PlatformAdminDashboardDto]:
    return ok(await service.get_dashboard_summary())
