import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.common.deps import SessionDep, TenantContextDep, UowSessionmakerDep, require_auth
from app.common.envelope import Envelope, ok
from app.features.lenses.repository import LensCatalogRepository
from app.features.lenses.schemas import (
    CreateOrderRequest,
    LensCatalogDto,
    OrderDto,
)
from app.features.lenses.service import LensCatalogService, OrderService

router = APIRouter(prefix="/lenses", tags=["lenses"], dependencies=[Depends(require_auth)])


def get_catalog_service(
    session: SessionDep, tenant_context: TenantContextDep
) -> LensCatalogService:
    return LensCatalogService(LensCatalogRepository(session, tenant_context))


def get_order_service(
    session: SessionDep,
    sessionmaker: UowSessionmakerDep,
    tenant_context: TenantContextDep,
) -> OrderService:
    return OrderService(session, sessionmaker, tenant_context)


CatalogServiceDep = Annotated[LensCatalogService, Depends(get_catalog_service)]
OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


@router.get("/catalog")
async def get_catalog(service: CatalogServiceDep) -> Envelope[LensCatalogDto]:
    return ok(await service.get_catalog())


@router.post("/orders")
async def create_order(body: CreateOrderRequest, service: OrderServiceDep) -> Envelope[OrderDto]:
    return ok(await service.create_order(body))


@router.get("/orders/{order_id}")
async def get_order(order_id: uuid.UUID, service: OrderServiceDep) -> Envelope[OrderDto]:
    return ok(await service.get_order(order_id))


@router.get("/patients/{patient_id}/order")
async def get_patient_order(patient_id: uuid.UUID, service: OrderServiceDep) -> Envelope[OrderDto]:
    return ok(await service.get_current_order_for_patient(patient_id))
