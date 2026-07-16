import uuid
from typing import TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.tenant_context import TenantContext
from app.db.base import TenantEntity

ModelT = TypeVar("ModelT", bound=TenantEntity)


class TenantScopedRepository:
    """Base for repositories over tenant-owned models.

    Every query and insert goes through this base so a feature repository can never construct
    an unscoped statement for a tenant-owned model. Global lookups (e.g. auth by email) belong
    in a repository that does not extend this class.
    """

    def __init__(self, session: AsyncSession, tenant_context: TenantContext) -> None:
        self._session = session
        self._tenant_context = tenant_context

    def scoped_select(self, model: type[ModelT]) -> Select[tuple[ModelT]]:
        """A `select(model)` pre-filtered to the current tenant."""
        return select(model).where(
            model.organization_id == self._tenant_context.organization_id
        )

    async def get_scoped(self, model: type[ModelT], entity_id: uuid.UUID) -> ModelT | None:
        """Scoped replacement for `session.get(model, entity_id)`.

        Returns `None` if the row does not exist or belongs to another organization.
        """
        result = await self._session.execute(
            self.scoped_select(model).where(model.id == entity_id)
        )
        return result.scalar_one_or_none()

    def add_scoped(self, entity: ModelT) -> None:
        """Stamp `organization_id` from the tenant context and stage the entity for insert."""
        entity.organization_id = self._tenant_context.organization_id
        self._session.add(entity)
