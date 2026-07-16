from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute


async def existing_values[ValueT](
    session: AsyncSession, column: InstrumentedAttribute[ValueT]
) -> set[ValueT]:
    """Natural-key values already present for ``column``, used to seed idempotently."""
    result = await session.execute(select(column))
    return set(result.scalars().all())
