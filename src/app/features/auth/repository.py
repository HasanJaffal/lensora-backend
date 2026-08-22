import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import User, UserRole


class UserRepository:
    """Data access for the user table. No business rules live here."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_platform_admin(self) -> User | None:
        result = await self._session.execute(
            select(User).where(User.role == UserRole.PLATFORM_ADMIN)
        )
        return result.scalars().first()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_organization_id(self, organization_id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            select(User).where(User.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def list_by_organization_ids(self, organization_ids: list[uuid.UUID]) -> list[User]:
        result = await self._session.execute(
            select(User).where(User.organization_id.in_(organization_ids))
        )
        return list(result.scalars().all())

    def add(self, user: User) -> None:
        self._session.add(user)
