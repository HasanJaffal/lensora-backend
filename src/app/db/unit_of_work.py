from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.engine import get_sessionmaker


class UnitOfWork:
    """Owns a single transaction boundary for a multi-step operation.

    Services depend on this abstraction rather than opening sessions themselves, so
    multi-table writes (e.g. a lens order and its line items) commit or roll back atomically.
    """

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._sessionmaker = sessionmaker or get_sessionmaker()
        self.session: AsyncSession

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self._sessionmaker()
        await self.session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                await self.session.commit()
            else:
                await self.session.rollback()
        finally:
            await self.session.close()
