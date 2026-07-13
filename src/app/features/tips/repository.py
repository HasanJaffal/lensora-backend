import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.tips.models import Tip, TipCategory


class TipRepository:
    """Data access for the tips library."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_tips(self, *, category: TipCategory | None = None) -> list[Tip]:
        statement = select(Tip).order_by(Tip.category, Tip.title_en)
        if category is not None:
            statement = statement.where(Tip.category == category)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def get_by_id(self, tip_id: uuid.UUID) -> Tip | None:
        return await self._session.get(Tip, tip_id)
