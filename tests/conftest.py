from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.common.deps import get_current_user, get_uow_sessionmaker
from app.db import seed as seed_module
from app.db.registry import Base
from app.db.session import get_session
from app.features.auth.models import User
from app.features.auth.repository import UserRepository
from app.features.organizations.repository import OrganizationRepository
from app.features.organizations.service import (
    OrganizationProvisioningRequest,
    OrganizationProvisioningService,
)
from app.main import create_app

TEST_ADMIN_PASSWORD = "correct-horse"


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def _provision_test_organization(session: AsyncSession) -> User:
    service = OrganizationProvisioningService(
        session, OrganizationRepository(session), UserRepository(session)
    )
    provisioned = await service.provision(
        OrganizationProvisioningRequest(
            organization_name="Test Optometry",
            organization_slug="test-optometry",
            admin_email="admin@lensora.test",
            admin_password=TEST_ADMIN_PASSWORD,
            admin_display_name_en="Dr. Jane Doe",
            admin_display_name_ar="د. جين دو",
            deposit_percent=Decimal("0.40"),
        )
    )
    return provisioned.admin_account


async def _seed_test_db(sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    async with sessionmaker() as session, session.begin():
        await _provision_test_organization(session)
        await seed_module.seed_lens_catalog(session)
        await seed_module.seed_tips(session)
        await seed_module._seed_inventory(session)
        await seed_module._seed_patients(session)


@pytest_asyncio.fixture
async def db_sessionmaker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Isolated in-memory database seeded with the deterministic fixture data.

    A single shared connection (``StaticPool``) keeps every session pointed at the same
    in-memory schema for the lifetime of one test.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    await _seed_test_db(sessionmaker)
    try:
        yield sessionmaker
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def seeded_admin(db_sessionmaker: async_sessionmaker[AsyncSession]) -> User:
    async with db_sessionmaker() as session:
        result = await session.execute(select(User).limit(1))
        return result.scalar_one()


@pytest_asyncio.fixture
async def api_client(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    seeded_admin: User,
) -> AsyncIterator[AsyncClient]:
    """Authenticated client wired to the isolated in-memory database."""
    app = create_app()

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with db_sessionmaker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_uow_sessionmaker] = lambda: db_sessionmaker
    app.dependency_overrides[get_current_user] = lambda: seeded_admin

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
