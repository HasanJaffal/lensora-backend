from decimal import Decimal
from enum import StrEnum

from pydantic import Field

from app.common.schema import CamelModel
from app.features.inventory.models import InventoryCategory, InventoryItem
from app.features.inventory.status import derive_stock_status, quantity_ratio


class FrameUse(StrEnum):
    """Product need driving which catalog the configurator / try-on shows (FR-TRY-2)."""

    EYEGLASSES = "eyeglasses"
    SUNGLASSES = "sunglasses"
    CONTACTS = "contacts"


class InventoryItemDto(CamelModel):
    id: str
    category: str
    name: str
    brand: str
    spec: str
    shape: str | None
    color: str | None
    sku: str
    qty: int  # maps to the `quantity` column; `qty` is the stable frontend API contract
    threshold: int
    price: Decimal
    status: str
    quantity_ratio: float

    @classmethod
    def from_model(cls, item: InventoryItem) -> "InventoryItemDto":
        return cls(
            id=str(item.id),
            category=item.category,
            name=item.name,
            brand=item.brand,
            spec=item.spec,
            shape=item.shape,
            color=item.color,
            sku=item.sku,
            qty=item.quantity,
            threshold=item.threshold,
            price=item.price,
            status=derive_stock_status(item.quantity, item.threshold),
            quantity_ratio=quantity_ratio(item.quantity, item.threshold),
        )


class InventoryStatsDto(CamelModel):
    total_skus: int
    low_stock_count: int
    out_of_stock_count: int
    total_value: Decimal


class InventoryCreateRequest(CamelModel):
    category: InventoryCategory
    name: str = Field(min_length=1, max_length=255)
    brand: str = Field(min_length=1, max_length=255)
    spec: str = Field(min_length=1, max_length=255)
    shape: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=50)
    sku: str = Field(min_length=1, max_length=50)
    qty: int = Field(ge=0)  # maps to the `quantity` column
    threshold: int = Field(ge=0)
    price: Decimal = Field(ge=0)


class InventoryUpdateRequest(CamelModel):
    qty: int | None = Field(default=None, ge=0)  # maps to the `quantity` column
    threshold: int | None = Field(default=None, ge=0)
    price: Decimal | None = Field(default=None, ge=0)
