import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.db.base import TenantEntity


async def existing_values_for_org[ValueT, ModelT: TenantEntity](
    session: AsyncSession,
    model: type[ModelT],
    column: InstrumentedAttribute[ValueT],
    organization_id: uuid.UUID,
) -> set[ValueT]:
    """Natural-key values already present for ``column`` within one org, for idempotent seeding."""
    result = await session.execute(select(column).where(model.organization_id == organization_id))
    return set(result.scalars().all())
