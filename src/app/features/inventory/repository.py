import uuid

from sqlalchemy import Select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.tenant_context import TenantContext
from app.db.repository import TenantScopedRepository
from app.features.inventory.models import InventoryCategory, InventoryItem


class InventoryRepository(TenantScopedRepository):
    """Data access for inventory items. No status derivation or business rules here."""

    def __init__(self, session: AsyncSession, tenant_context: TenantContext) -> None:
        super().__init__(session, tenant_context)
        self._session = session

    def _base_query(
        self, *, category: InventoryCategory | None, low_stock: bool
    ) -> Select[tuple[InventoryItem]]:
        statement = self.scoped_select(InventoryItem)
        if category is not None:
            statement = statement.where(InventoryItem.category == category)
        if low_stock:
            statement = statement.where(InventoryItem.quantity <= InventoryItem.threshold)
        return statement.order_by(InventoryItem.category, InventoryItem.name)

    async def list_items(
        self, *, category: InventoryCategory | None = None, low_stock: bool = False
    ) -> list[InventoryItem]:
        result = await self._session.execute(
            self._base_query(category=category, low_stock=low_stock)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[InventoryItem]:
        result = await self._session.execute(self.scoped_select(InventoryItem))
        return list(result.scalars().all())

    async def list_in_stock_by_categories(
        self, categories: tuple[InventoryCategory, ...]
    ) -> list[InventoryItem]:
        result = await self._session.execute(
            self.scoped_select(InventoryItem)
            .where(
                or_(*(InventoryItem.category == category for category in categories)),
                InventoryItem.quantity > 0,
            )
            .order_by(InventoryItem.brand, InventoryItem.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, item_id: uuid.UUID) -> InventoryItem | None:
        return await self.get_scoped(InventoryItem, item_id)

    async def get_by_sku(self, sku: str) -> InventoryItem | None:
        result = await self._session.execute(
            self.scoped_select(InventoryItem).where(InventoryItem.sku == sku)
        )
        return result.scalar_one_or_none()

    def add(self, item: InventoryItem) -> None:
        self.add_scoped(item)

    async def delete(self, item: InventoryItem) -> None:
        await self._session.delete(item)

    async def commit(self) -> None:
        await self._session.commit()
