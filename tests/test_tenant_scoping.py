import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.pool import StaticPool

from app.common.exceptions import TenantContextMissingError
from app.common.tenant_context import (
    TenantContext,
    get_tenant_context,
    require_tenant_context,
    tenant_context,
)
from app.db.base import TenantEntity
from app.db.repository import TenantScopedRepository
from app.features.auth.models import UserRole


class Widget(TenantEntity):
    """Test-only tenant-owned model, isolated from the shared registry metadata."""

    __tablename__ = "test_tenant_scoping_widget"

    name: Mapped[str] = mapped_column(String(100))


@pytest_asyncio.fixture
async def widget_sessionmaker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_conn: Widget.metadata.create_all(sync_conn, tables=[Widget.__table__])
        )
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


def _tenant_context(organization_id: uuid.UUID | None = None) -> TenantContext:
    return TenantContext(
        organization_id=organization_id or uuid.uuid4(),
        user_id=uuid.uuid4(),
        role=UserRole.ORGANIZATION_ADMIN,
    )


class WidgetRepository(TenantScopedRepository):
    async def get(self, widget_id: uuid.UUID) -> Widget | None:
        return await self.get_scoped(Widget, widget_id)

    def create(self, name: str) -> Widget:
        widget = Widget(name=name)
        self.add_scoped(widget)
        return widget


async def test_scoped_select_adds_organization_predicate(
    widget_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    org_a_context = _tenant_context()
    org_b_context = _tenant_context()

    async with widget_sessionmaker() as session, session.begin():
        WidgetRepository(session, org_a_context).create("A's widget")
        WidgetRepository(session, org_b_context).create("B's widget")

    async with widget_sessionmaker() as session:
        statement = TenantScopedRepository(session, org_a_context).scoped_select(Widget)
        result = await session.execute(statement)
        rows = result.scalars().all()

    assert [row.name for row in rows] == ["A's widget"]


async def test_get_scoped_returns_none_for_another_organizations_id(
    widget_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    org_a_context = _tenant_context()
    org_b_context = _tenant_context()

    async with widget_sessionmaker() as session, session.begin():
        widget = WidgetRepository(session, org_a_context).create("A's widget")
        await session.flush()
        widget_id = widget.id

    async with widget_sessionmaker() as session:
        as_owner = await WidgetRepository(session, org_a_context).get(widget_id)
        as_other_org = await WidgetRepository(session, org_b_context).get(widget_id)

    assert as_owner is not None
    assert as_owner.id == widget_id
    assert as_other_org is None


async def test_add_scoped_stamps_organization_id(
    widget_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    ctx = _tenant_context()

    async with widget_sessionmaker() as session, session.begin():
        widget = WidgetRepository(session, ctx).create("Stamped widget")
        await session.flush()

        assert widget.organization_id == ctx.organization_id


def test_tenant_context_sets_and_resets_the_context_var() -> None:
    assert get_tenant_context() is None

    ctx = _tenant_context()
    with tenant_context(ctx):
        assert get_tenant_context() == ctx
        assert require_tenant_context() == ctx

    assert get_tenant_context() is None


def test_tenant_context_resets_even_on_exception() -> None:
    ctx = _tenant_context()

    with pytest.raises(ValueError, match="boom"), tenant_context(ctx):
        assert get_tenant_context() == ctx
        raise ValueError("boom")

    assert get_tenant_context() is None


def test_require_tenant_context_raises_when_unset() -> None:
    assert get_tenant_context() is None

    with pytest.raises(TenantContextMissingError):
        require_tenant_context()


def test_tenant_context_supports_nesting() -> None:
    outer = _tenant_context()
    inner = _tenant_context()

    with tenant_context(outer):
        assert get_tenant_context() == outer
        with tenant_context(inner):
            assert get_tenant_context() == inner
        assert get_tenant_context() == outer

    assert get_tenant_context() is None
