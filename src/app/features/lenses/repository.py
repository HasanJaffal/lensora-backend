import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.tenant_context import TenantContext
from app.db.repository import TenantScopedRepository
from app.features.lenses.models import (
    LensCoating,
    LensMaterial,
    LensTint,
    LensType,
    Order,
)


class LensCatalogRepository(TenantScopedRepository):
    """Data access for the four lens option catalogs."""

    def __init__(self, session: AsyncSession, tenant_context: TenantContext) -> None:
        super().__init__(session, tenant_context)
        self._session = session

    async def list_types(self) -> list[LensType]:
        result = await self._session.execute(self.scoped_select(LensType).order_by(LensType.price))
        return list(result.scalars().all())

    async def list_materials(self) -> list[LensMaterial]:
        result = await self._session.execute(
            self.scoped_select(LensMaterial).order_by(LensMaterial.price)
        )
        return list(result.scalars().all())

    async def list_coatings(self) -> list[LensCoating]:
        result = await self._session.execute(
            self.scoped_select(LensCoating).order_by(LensCoating.price)
        )
        return list(result.scalars().all())

    async def list_tints(self) -> list[LensTint]:
        result = await self._session.execute(self.scoped_select(LensTint).order_by(LensTint.price))
        return list(result.scalars().all())

    async def get_type(self, type_id: uuid.UUID) -> LensType | None:
        return await self.get_scoped(LensType, type_id)

    async def get_material(self, material_id: uuid.UUID) -> LensMaterial | None:
        return await self.get_scoped(LensMaterial, material_id)

    async def get_tint(self, tint_id: uuid.UUID) -> LensTint | None:
        return await self.get_scoped(LensTint, tint_id)

    async def get_coatings(self, coating_ids: list[uuid.UUID]) -> list[LensCoating]:
        if not coating_ids:
            return []
        result = await self._session.execute(
            self.scoped_select(LensCoating).where(LensCoating.id.in_(coating_ids))
        )
        return list(result.scalars().all())


class OrderRepository(TenantScopedRepository):
    """Data access for lens orders and their line items."""

    def __init__(self, session: AsyncSession, tenant_context: TenantContext) -> None:
        super().__init__(session, tenant_context)
        self._session = session

    def add(self, order: Order) -> None:
        self.add_scoped(order)

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        result = await self._session.execute(
            self.scoped_select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        return result.scalar_one_or_none()

    async def get_latest_for_patient(self, patient_id: uuid.UUID) -> Order | None:
        result = await self._session.execute(
            self.scoped_select(Order)
            .where(Order.patient_id == patient_id)
            .order_by(Order.created_at.desc())
            .options(selectinload(Order.items))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def total_revenue_since(self, since: datetime) -> Decimal:
        total = await self._session.scalar(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                Order.organization_id == self._tenant_context.organization_id,
                Order.created_at >= since,
            )
        )
        return Decimal(str(total))
