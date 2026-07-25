import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.inventory.models import InventoryCategory, InventoryItem
from app.features.storefront.schemas import PUBLIC_CATEGORIES


class StorefrontProductRepository:
    """Read-only public catalog access, scoped by an explicitly passed ``organization_id``.

    Intentionally not a ``TenantScopedRepository``: that base derives its boundary from the
    authenticated ``TenantContext``, and a storefront visitor has no account to derive one
    from. Scoping is still absolute — every query filters on the ``organization_id`` resolved
    from the requested slug, and the category filter never widens past ``PUBLIC_CATEGORIES``.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_public_products(
        self, *, organization_id: uuid.UUID, category: InventoryCategory | None
    ) -> list[InventoryItem]:
        categories = PUBLIC_CATEGORIES if category is None else (category,)
        result = await self._session.execute(
            select(InventoryItem)
            .where(
                InventoryItem.organization_id == organization_id,
                InventoryItem.category.in_(categories),
                InventoryItem.quantity > 0,
            )
            .order_by(InventoryItem.category, InventoryItem.brand, InventoryItem.name)
        )
        return list(result.scalars().all())
