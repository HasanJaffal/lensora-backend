import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.tenant_context import TenantContext
from app.db.repository import TenantScopedRepository
from app.features.attachments.models import Attachment


class AttachmentRepository(TenantScopedRepository):
    """Data access for attachment metadata, always scoped to the current organization."""

    def __init__(self, session: AsyncSession, tenant_context: TenantContext) -> None:
        super().__init__(session, tenant_context)
        self._session = session

    def add(self, attachment: Attachment) -> None:
        self.add_scoped(attachment)

    async def get_by_id(self, attachment_id: uuid.UUID) -> Attachment | None:
        return await self.get_scoped(Attachment, attachment_id)

    async def list_by_subfolder(self, subfolder: str) -> list[Attachment]:
        statement = self.scoped_select(Attachment).where(Attachment.subfolder == subfolder)
        result = await self._session.execute(
            statement.order_by(Attachment.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, attachment: Attachment) -> None:
        await self._session.delete(attachment)

    async def commit(self) -> None:
        await self._session.commit()

    async def refresh(self, attachment: Attachment) -> None:
        await self._session.refresh(attachment)
