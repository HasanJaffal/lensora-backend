import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.tenant_context import TenantContext
from app.db.repository import TenantScopedRepository
from app.features.import_forms.models import ImportForm


class ImportRepository(TenantScopedRepository):
    """Data access for import records (extracted questions only, never the file)."""

    def __init__(self, session: AsyncSession, tenant_context: TenantContext) -> None:
        super().__init__(session, tenant_context)
        self._session = session

    def add(self, record: ImportForm) -> None:
        self.add_scoped(record)

    async def get_by_id(self, import_id: uuid.UUID) -> ImportForm | None:
        return await self.get_scoped(ImportForm, import_id)

    async def commit(self) -> None:
        await self._session.commit()

    async def refresh(self, record: ImportForm) -> None:
        await self._session.refresh(record)
