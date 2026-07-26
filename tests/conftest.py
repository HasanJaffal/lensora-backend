from collections.abc import AsyncIterator
from dataclasses import dataclass
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

from app.common.deps import (
    SessionDep,
    TenantContextDep,
    get_current_user,
    get_uow_sessionmaker,
)
from app.db import seed as seed_module
from app.db.registry import Base
from app.db.seeds.organization_defaults import seed_lens_catalog, seed_tips
from app.db.session import get_session
from app.features.attachments.router import get_attachment_service
from app.features.attachments.service import AttachmentService
from app.features.auth.models import User
from app.features.auth.repository import UserRepository
from app.features.organizations.models import Organization
from app.features.organizations.repository import OrganizationRepository
from app.features.organizations.service import (
    OrganizationProvisioningRequest,
    OrganizationProvisioningService,
)
from app.main import create_app
from tests.fake_object_storage import FakeObjectStorage

TEST_ADMIN_PASSWORD = "correct-horse"


@dataclass(frozen=True)
class ProvisionedTenant:
    """An organization + its admin account, provisioned and seeded for one test."""

    organization: Organization
    admin_account: User


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def _provision_organization(
    session: AsyncSession,
    *,
    org_slug: str,
    org_name: str,
    admin_email: str,
) -> ProvisionedTenant:
    service = OrganizationProvisioningService(
        session, OrganizationRepository(session), UserRepository(session)
    )
    provisioned = await service.provision(
        OrganizationProvisioningRequest(
            organization_name=org_name,
            organization_slug=org_slug,
            admin_email=admin_email,
            admin_password=TEST_ADMIN_PASSWORD,
            admin_display_name_en="Dr. Jane Doe",
            admin_display_name_ar="د. جين دو",
            deposit_percent=Decimal("0.40"),
        )
    )
    await session.flush()
    return ProvisionedTenant(
        organization=provisioned.organization, admin_account=provisioned.admin_account
    )


async def _seed_test_db(sessionmaker: async_sessionmaker[AsyncSession]) -> ProvisionedTenant:
    async with sessionmaker() as session, session.begin():
        tenant = await _provision_organization(
            session,
            org_slug="test-optometry",
            org_name="Test Optometry",
            admin_email="admin@lensora.test",
        )
        organization_id = tenant.organization.id
        await seed_lens_catalog(session, organization_id)
        await seed_tips(session, organization_id)
        await seed_module._seed_inventory(session, organization_id)
        await seed_module._seed_patients(session, organization_id)
    return tenant


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


TEST_SIGNED_URL_EXPIRES_SECONDS = 3600


def _wire_app(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    current_user: User,
    object_storage: FakeObjectStorage | None = None,
) -> FastAPI:
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
    app.dependency_overrides[get_current_user] = lambda: current_user

    if object_storage is not None:
        # Swaps only the storage collaborator; the real service, repository, and tenant
        # scoping still run, so these tests cover the same code path production does.
        def override_get_attachment_service(
            session: SessionDep, tenant_context: TenantContextDep
        ) -> AttachmentService:
            return AttachmentService(
                session, tenant_context, object_storage, TEST_SIGNED_URL_EXPIRES_SECONDS
            )

        app.dependency_overrides[get_attachment_service] = override_get_attachment_service

    return app


@pytest_asyncio.fixture
async def api_client(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    seeded_admin: User,
) -> AsyncIterator[AsyncClient]:
    """Authenticated client wired to the isolated in-memory database."""
    app = _wire_app(db_sessionmaker, seeded_admin)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture
def object_storage() -> FakeObjectStorage:
    return FakeObjectStorage()


@pytest_asyncio.fixture
async def attachments_client(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    seeded_admin: User,
    object_storage: FakeObjectStorage,
) -> AsyncIterator[AsyncClient]:
    """Authenticated client whose attachment routes are backed by in-memory storage."""
    app = _wire_app(db_sessionmaker, seeded_admin, object_storage)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest_asyncio.fixture
async def two_org_db_sessionmaker() -> AsyncIterator[
    tuple[async_sessionmaker[AsyncSession], ProvisionedTenant, ProvisionedTenant]
]:
    """A shared database seeded with two fully independent, isolated organizations.

    Org A and Org B each get their own admin account and their own catalog/tips/
    inventory/patient seed data, so cross-tenant isolation tests have real per-org
    data to assert never leaks across the boundary.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with sessionmaker() as session, session.begin():
        org_a = await _provision_organization(
            session,
            org_slug="org-a",
            org_name="Org A Optometry",
            admin_email="admin@org-a.test",
        )
        org_b = await _provision_organization(
            session,
            org_slug="org-b",
            org_name="Org B Optometry",
            admin_email="admin@org-b.test",
        )
        for tenant in (org_a, org_b):
            organization_id = tenant.organization.id
            await seed_lens_catalog(session, organization_id)
            await seed_tips(session, organization_id)
            await seed_module._seed_inventory(session, organization_id)
            await seed_module._seed_patients(session, organization_id)

    try:
        yield sessionmaker, org_a, org_b
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def anonymous_client(
    two_org_db_sessionmaker: tuple[
        async_sessionmaker[AsyncSession], ProvisionedTenant, ProvisionedTenant
    ],
) -> AsyncIterator[AsyncClient]:
    """Unauthenticated client for the public storefront.

    Deliberately does not override ``get_current_user``: the storefront must work with no
    principal at all, so leaving the real dependency in place proves the routes never
    require one.
    """
    sessionmaker, _org_a, _org_b = two_org_db_sessionmaker
    app = create_app()

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_uow_sessionmaker] = lambda: sessionmaker
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest_asyncio.fixture
async def org_a_client(
    two_org_db_sessionmaker: tuple[
        async_sessionmaker[AsyncSession], ProvisionedTenant, ProvisionedTenant
    ],
) -> AsyncIterator[AsyncClient]:
    """Authenticated client acting as Org A's admin."""
    sessionmaker, org_a, _org_b = two_org_db_sessionmaker
    app = _wire_app(sessionmaker, org_a.admin_account)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest_asyncio.fixture
async def org_b_client(
    two_org_db_sessionmaker: tuple[
        async_sessionmaker[AsyncSession], ProvisionedTenant, ProvisionedTenant
    ],
) -> AsyncIterator[AsyncClient]:
    """Authenticated client acting as Org B's admin."""
    sessionmaker, _org_a, org_b = two_org_db_sessionmaker
    app = _wire_app(sessionmaker, org_b.admin_account)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest_asyncio.fixture
async def org_attachment_clients(
    two_org_db_sessionmaker: tuple[
        async_sessionmaker[AsyncSession], ProvisionedTenant, ProvisionedTenant
    ],
    object_storage: FakeObjectStorage,
) -> AsyncIterator[tuple[AsyncClient, AsyncClient]]:
    """Org A and Org B attachment clients sharing one bucket.

    A single storage instance is deliberate: it is what makes a leak observable, since both
    tenants' objects live in the same bucket exactly as they do in production.
    """
    sessionmaker, org_a, org_b = two_org_db_sessionmaker
    app_a = _wire_app(sessionmaker, org_a.admin_account, object_storage)
    app_b = _wire_app(sessionmaker, org_b.admin_account, object_storage)
    async with (
        AsyncClient(
            transport=ASGITransport(app=app_a, raise_app_exceptions=False),
            base_url="http://test",
        ) as client_a,
        AsyncClient(
            transport=ASGITransport(app=app_b, raise_app_exceptions=False),
            base_url="http://test",
        ) as client_b,
    ):
        yield client_a, client_b
