import uuid
from datetime import datetime

from sqlalchemy import func, select
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

    async def list_page(self, *, offset: int, limit: int) -> tuple[list[Organization], int]:
        total = await self.count_all()
        result = await self._session.execute(
            select(Organization).order_by(Organization.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def count_all(self) -> int:
        total = await self._session.scalar(select(func.count()).select_from(Organization))
        return total or 0

    async def count_by_active_status(self, *, is_active: bool) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(Organization).where(Organization.is_active.is_(is_active))
        )
        return total or 0

    async def count_created_since(self, *, created_since: datetime) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(Organization)
            .where(Organization.created_at >= created_since)
        )
        return total or 0

    def add(self, organization: Organization) -> None:
        self._session.add(organization)
