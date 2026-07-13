import uuid
from decimal import Decimal

from app.common.exceptions import NotFoundError
from app.features.inventory.models import InventoryCategory, InventoryItem
from app.features.inventory.repository import InventoryRepository
from app.features.inventory.schemas import (
    FrameUse,
    InventoryItemDto,
    InventoryStatsDto,
    InventoryUpdateRequest,
)

_USE_TO_CATEGORIES: dict[FrameUse, tuple[InventoryCategory, ...]] = {
    FrameUse.EYEGLASSES: (InventoryCategory.FRAME,),
    FrameUse.SUNGLASSES: (InventoryCategory.SUN,),
    FrameUse.CONTACTS: (InventoryCategory.CONTACT,),
}


class InventoryService:
    """Business logic for inventory: derived status, headline stats, and stock feeds."""

    def __init__(self, items: InventoryRepository) -> None:
        self._items = items

    async def list_items(
        self, *, category: InventoryCategory | None, low_stock: bool
    ) -> list[InventoryItemDto]:
        records = await self._items.list_items(category=category, low_stock=low_stock)
        return [InventoryItemDto.from_model(record) for record in records]

    async def get_stats(self) -> InventoryStatsDto:
        records = await self._items.list_all()
        low_stock = sum(1 for item in records if item.qty <= item.threshold)
        out_of_stock = sum(1 for item in records if item.qty <= 0)
        total_value = sum(
            (item.price * item.qty for item in records), start=Decimal("0")
        )
        return InventoryStatsDto(
            total_skus=len(records),
            low_stock_count=low_stock,
            out_of_stock_count=out_of_stock,
            total_value=total_value,
        )

    async def list_frames(self, *, use: FrameUse, in_stock: bool) -> list[InventoryItemDto]:
        categories = _USE_TO_CATEGORIES[use]
        if in_stock:
            records = await self._items.list_in_stock_by_categories(categories)
        else:
            records = [
                item
                for category in categories
                for item in await self._items.list_items(category=category)
            ]
        return [InventoryItemDto.from_model(record) for record in records]

    async def get_item(self, item_id: uuid.UUID) -> InventoryItemDto:
        return InventoryItemDto.from_model(await self._require_item(item_id))

    async def update_item(
        self, item_id: uuid.UUID, request: InventoryUpdateRequest
    ) -> InventoryItemDto:
        item = await self._require_item(item_id)
        changed = request.model_fields_set
        if "qty" in changed and request.qty is not None:
            item.qty = request.qty
        if "threshold" in changed and request.threshold is not None:
            item.threshold = request.threshold
        if "price" in changed and request.price is not None:
            item.price = request.price
        await self._items.commit()
        return InventoryItemDto.from_model(item)

    async def _require_item(self, item_id: uuid.UUID) -> InventoryItem:
        item = await self._items.get_by_id(item_id)
        if item is None:
            raise NotFoundError(f"Inventory item {item_id} not found")
        return item
