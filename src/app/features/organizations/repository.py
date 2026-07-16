import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.organizations.models import Organization


class OrganizationRepository:
    """Data access for the organization tenant root. No business rules live here."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, organization_id: uuid.UUID) -> Organization | None:
        return await self._session.get(Organization, organization_id)

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self._session.execute(select(Organization).where(Organization.slug == slug))
        return result.scalar_one_or_none()

    def add(self, organization: Organization) -> None:
        self._session.add(organization)
