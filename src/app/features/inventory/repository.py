import uuid

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.inventory.models import InventoryCategory, InventoryItem


class InventoryRepository:
    """Data access for inventory items. No status derivation or business rules here."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(
        self, *, category: InventoryCategory | None, low_stock: bool
    ) -> Select[tuple[InventoryItem]]:
        statement = select(InventoryItem)
        if category is not None:
            statement = statement.where(InventoryItem.category == category)
        if low_stock:
            statement = statement.where(InventoryItem.qty <= InventoryItem.threshold)
        return statement.order_by(InventoryItem.category, InventoryItem.name)

    async def list_items(
        self, *, category: InventoryCategory | None = None, low_stock: bool = False
    ) -> list[InventoryItem]:
        result = await self._session.execute(
            self._base_query(category=category, low_stock=low_stock)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[InventoryItem]:
        result = await self._session.execute(select(InventoryItem))
        return list(result.scalars().all())

    async def list_in_stock_by_categories(
        self, categories: tuple[InventoryCategory, ...]
    ) -> list[InventoryItem]:
        result = await self._session.execute(
            select(InventoryItem)
            .where(
                or_(*(InventoryItem.category == category for category in categories)),
                InventoryItem.qty > 0,
            )
            .order_by(InventoryItem.brand, InventoryItem.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, item_id: uuid.UUID) -> InventoryItem | None:
        return await self._session.get(InventoryItem, item_id)

    async def commit(self) -> None:
        await self._session.commit()
