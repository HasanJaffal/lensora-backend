import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundError
from app.common.pagination import PaginationMeta
from app.db.seeds.organization_defaults import seed_lens_catalog, seed_tips
from app.features.auth.repository import UserRepository
from app.features.organizations.repository import OrganizationRepository
from app.features.organizations.service import (
    OrganizationProvisioningRequest,
    OrganizationProvisioningService,
)
from app.features.platform_admin.schemas import (
    CreateOrganizationRequest,
    OrganizationDto,
    PlatformAdminDashboardDto,
)


class PlatformAdminService:
    """Organization/account metadata management for the platform-admin principal.

    Never touches patient/inventory/clinical data — only organization and admin-account
    metadata, matching the platform-admin route contract.
    """

    def __init__(
        self,
        session: AsyncSession,
        organizations: OrganizationRepository,
        users: UserRepository,
    ) -> None:
        self._session = session
        self._organizations = organizations
        self._users = users

    async def list_organizations(
        self, *, page: int, page_size: int, offset: int
    ) -> tuple[list[OrganizationDto], PaginationMeta]:
        organizations, total = await self._organizations.list_page(offset=offset, limit=page_size)
        admins = await self._users.list_by_organization_ids([org.id for org in organizations])
        admin_by_org_id = {admin.organization_id: admin for admin in admins}
        items = [
            OrganizationDto.from_models(organization, admin_by_org_id[organization.id])
            for organization in organizations
            if organization.id in admin_by_org_id
        ]
        meta = PaginationMeta.build(page=page, page_size=page_size, total=total)
        return items, meta

    async def get_organization(self, organization_id: uuid.UUID) -> OrganizationDto:
        organization = await self._organizations.get_by_id(organization_id)
        if organization is None:
            raise NotFoundError(f"Organization {organization_id} not found")
        admin = await self._users.get_by_organization_id(organization_id)
        if admin is None:
            raise NotFoundError(f"Organization {organization_id} not found")
        return OrganizationDto.from_models(organization, admin)

    async def create_organization(self, request: CreateOrganizationRequest) -> OrganizationDto:
        provisioning_service = OrganizationProvisioningService(
            self._session, self._organizations, self._users
        )
        provisioned = await provisioning_service.provision(
            OrganizationProvisioningRequest(
                organization_name=request.name,
                organization_slug=request.slug,
                admin_email=request.admin_email,
                admin_password=request.admin_password,
                admin_display_name_en=request.admin_display_name_en,
                admin_display_name_ar=request.admin_display_name_ar,
                deposit_percent=request.deposit_percent,
            )
        )
        await seed_lens_catalog(self._session, provisioned.organization.id)
        await seed_tips(self._session, provisioned.organization.id)
        await self._session.commit()
        return OrganizationDto.from_models(provisioned.organization, provisioned.admin_account)

    async def set_organization_status(
        self, organization_id: uuid.UUID, *, is_active: bool
    ) -> OrganizationDto:
        organization = await self._organizations.get_by_id(organization_id)
        if organization is None:
            raise NotFoundError(f"Organization {organization_id} not found")
        admin = await self._users.get_by_organization_id(organization_id)
        if admin is None:
            raise NotFoundError(f"Organization {organization_id} not found")
        organization.is_active = is_active
        await self._session.commit()
        return OrganizationDto.from_models(organization, admin)

    async def get_dashboard_summary(self) -> PlatformAdminDashboardDto:
        now = datetime.now(UTC)
        total = await self._organizations.count_all()
        active = await self._organizations.count_by_active_status(is_active=True)
        created_this_month = await self._organizations.count_created_since(
            created_since=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        )
        return PlatformAdminDashboardDto(
            total_organizations=total,
            active_organizations=active,
            inactive_organizations=total - active,
            organizations_created_this_month=created_this_month,
        )
