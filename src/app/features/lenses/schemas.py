import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.common.schema import CamelModel
from app.features.lenses.models import LensOptionMixin, Order, OrderItem


class LensOptionDto(CamelModel):
    id: str
    name_en: str
    name_ar: str
    description_en: str
    description_ar: str
    price: Decimal

    @classmethod
    def from_model(cls, option: LensOptionMixin) -> "LensOptionDto":
        return cls(
            id=str(option.id),  # type: ignore[attr-defined]
            name_en=option.name_en,
            name_ar=option.name_ar,
            description_en=option.description_en,
            description_ar=option.description_ar,
            price=option.price,
        )


class LensCatalogDto(CamelModel):
    types: list[LensOptionDto]
    materials: list[LensOptionDto]
    coatings: list[LensOptionDto]
    tints: list[LensOptionDto]


class CreateOrderRequest(CamelModel):
    patient_id: uuid.UUID
    lens_type_id: uuid.UUID
    material_id: uuid.UUID
    coating_ids: list[uuid.UUID] = Field(default_factory=list)
    tint_id: uuid.UUID
    frame_id: uuid.UUID


class OrderItemDto(CamelModel):
    label_en: str
    label_ar: str
    price: Decimal

    @classmethod
    def from_model(cls, item: OrderItem) -> "OrderItemDto":
        return cls(label_en=item.label_en, label_ar=item.label_ar, price=item.price)


class OrderFrameDto(CamelModel):
    sku: str | None
    name: str | None


class OrderDto(CamelModel):
    id: str
    patient_id: str
    items: list[OrderItemDto]
    total: Decimal
    deposit: Decimal
    deposit_percent: Decimal
    frame: OrderFrameDto
    created_at: datetime

    @classmethod
    def from_model(cls, order: Order) -> "OrderDto":
        return cls(
            id=str(order.id),
            patient_id=str(order.patient_id),
            items=[OrderItemDto.from_model(item) for item in order.items],
            total=order.total,
            deposit=order.deposit,
            deposit_percent=order.deposit_percent,
            frame=OrderFrameDto(sku=order.frame_sku, name=order.frame_name),
            created_at=order.created_at,
        )
