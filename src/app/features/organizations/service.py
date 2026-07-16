from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AccountEmailTakenError, OrganizationSlugTakenError
from app.core.security import hash_password
from app.features.auth.models import User, UserRole
from app.features.auth.repository import UserRepository
from app.features.organizations.models import Organization
from app.features.organizations.repository import OrganizationRepository


@dataclass(frozen=True)
class OrganizationProvisioningRequest:
    organization_name: str
    organization_slug: str
    admin_email: str
    admin_password: str
    admin_display_name_en: str
    admin_display_name_ar: str
    deposit_percent: Decimal


@dataclass(frozen=True)
class ProvisionedOrganization:
    organization: Organization
    admin_account: User


class OrganizationProvisioningService:
    """Creates a tenant and its single admin account.

    Flushes after creating the organization so the admin account's foreign key has a
    concrete ``organization_id`` to reference within the same transaction.
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

    async def provision(
        self, request: OrganizationProvisioningRequest
    ) -> ProvisionedOrganization:
        if await self._organizations.get_by_slug(request.organization_slug) is not None:
            raise OrganizationSlugTakenError(
                f"Organization slug '{request.organization_slug}' is already in use"
            )
        if await self._users.get_by_email(request.admin_email) is not None:
            raise AccountEmailTakenError(
                f"Account email '{request.admin_email}' is already in use"
            )

        organization = Organization(
            name=request.organization_name,
            slug=request.organization_slug,
            deposit_percent=request.deposit_percent,
        )
        self._organizations.add(organization)
        await self._session.flush()

        admin_account = User(
            organization_id=organization.id,
            email=request.admin_email,
            hashed_password=hash_password(request.admin_password),
            display_name_en=request.admin_display_name_en,
            display_name_ar=request.admin_display_name_ar,
            role=UserRole.ORGANIZATION_ADMIN,
        )
        self._users.add(admin_account)

        return ProvisionedOrganization(organization=organization, admin_account=admin_account)
