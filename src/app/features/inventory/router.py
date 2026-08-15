import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.common.deps import SessionDep, TenantContextDep, require_auth
from app.common.envelope import Envelope, ok
from app.common.exceptions import ValidationError
from app.features.inventory.models import InventoryCategory
from app.features.inventory.repository import InventoryRepository
from app.features.inventory.schemas import (
    FrameUse,
    InventoryCreateRequest,
    InventoryItemDto,
    InventoryStatsDto,
    InventoryUpdateRequest,
)
from app.features.inventory.service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"], dependencies=[Depends(require_auth)])


def get_inventory_service(
    session: SessionDep, tenant_context: TenantContextDep
) -> InventoryService:
    return InventoryService(InventoryRepository(session, tenant_context))


InventoryServiceDep = Annotated[InventoryService, Depends(get_inventory_service)]


def _parse_category(category: str | None) -> InventoryCategory | None:
    if category is None:
        return None
    try:
        return InventoryCategory(category)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in InventoryCategory)
        raise ValidationError(f"Unknown category '{category}'; expected one of: {allowed}") from exc


@router.get("")
async def list_inventory(
    service: InventoryServiceDep,
    category: Annotated[str | None, Query()] = None,
    low_stock: Annotated[bool, Query(alias="lowStock")] = False,
) -> Envelope[list[InventoryItemDto]]:
    items = await service.list_items(category=_parse_category(category), low_stock=low_stock)
    return ok(items)


@router.post("")
async def create_inventory_item(
    body: InventoryCreateRequest, service: InventoryServiceDep
) -> Envelope[InventoryItemDto]:
    return ok(await service.create_item(body))


@router.get("/stats")
async def get_inventory_stats(service: InventoryServiceDep) -> Envelope[InventoryStatsDto]:
    return ok(await service.get_stats())


@router.get("/frames")
async def list_frames(
    service: InventoryServiceDep,
    use: Annotated[FrameUse, Query()] = FrameUse.EYEGLASSES,
    in_stock: Annotated[bool, Query(alias="inStock")] = True,
) -> Envelope[list[InventoryItemDto]]:
    return ok(await service.list_frames(use=use, in_stock=in_stock))


@router.get("/{item_id}")
async def get_inventory_item(
    item_id: uuid.UUID, service: InventoryServiceDep
) -> Envelope[InventoryItemDto]:
    return ok(await service.get_item(item_id))


@router.patch("/{item_id}")
async def update_inventory_item(
    item_id: uuid.UUID,
    body: InventoryUpdateRequest,
    service: InventoryServiceDep,
) -> Envelope[InventoryItemDto]:
    return ok(await service.update_item(item_id, body))


@router.delete("/{item_id}")
async def delete_inventory_item(
    item_id: uuid.UUID, service: InventoryServiceDep
) -> Envelope[None]:
    await service.delete_item(item_id)
    return ok(None)
