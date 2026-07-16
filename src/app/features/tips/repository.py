import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.tenant_context import TenantContext
from app.db.repository import TenantScopedRepository
from app.features.tips.models import Tip, TipCategory


class TipRepository(TenantScopedRepository):
    """Data access for the tips library."""

    def __init__(self, session: AsyncSession, tenant_context: TenantContext) -> None:
        super().__init__(session, tenant_context)
        self._session = session

    async def list_tips(self, *, category: TipCategory | None = None) -> list[Tip]:
        statement = self.scoped_select(Tip).order_by(Tip.category, Tip.title_en)
        if category is not None:
            statement = statement.where(Tip.category == category)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def get_by_id(self, tip_id: uuid.UUID) -> Tip | None:
        return await self.get_scoped(Tip, tip_id)
