import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.import_forms.models import ImportForm


class ImportRepository:
    """Data access for import records (extracted questions only, never the file)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, record: ImportForm) -> None:
        self._session.add(record)

    async def get_by_id(self, import_id: uuid.UUID) -> ImportForm | None:
        return await self._session.get(ImportForm, import_id)

    async def commit(self) -> None:
        await self._session.commit()

    async def refresh(self, record: ImportForm) -> None:
        await self._session.refresh(record)
