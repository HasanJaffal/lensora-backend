import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.deps import get_current_user, get_uow_sessionmaker
from app.core.security import hash_password
from app.db.session import get_session
from app.features.auth.models import User, UserRole
from app.features.organizations.models import Organization
from app.main import create_app

PLATFORM_ADMIN_EMAIL = "platform@lensora.test"


def _make_platform_admin() -> User:
    return User(
        id=uuid.uuid4(),
        organization_id=None,
        email=PLATFORM_ADMIN_EMAIL,
        hashed_password=hash_password("correct-horse"),
        display_name_en="Platform Owner",
        display_name_ar="مالك المنصة",
        role=UserRole.PLATFORM_ADMIN,
    )


def _client_for(
    db_sessionmaker: async_sessionmaker[AsyncSession], current_user: User
) -> AsyncClient:
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
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest_asyncio.fixture
async def platform_admin_client(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    """Client authenticated as the platform admin, wired to the isolated database."""
    platform_admin = _make_platform_admin()
    async with db_sessionmaker() as session, session.begin():
        session.add(platform_admin)
    async with _client_for(db_sessionmaker, platform_admin) as client:
        yield client


@pytest_asyncio.fixture
async def tenant_admin_client(
    db_sessionmaker: async_sessionmaker[AsyncSession],
    seeded_admin: User,
) -> AsyncIterator[AsyncClient]:
    """Client authenticated as an organization admin — must be denied every platform route."""
    async with _client_for(db_sessionmaker, seeded_admin) as client:
        yield client


def _new_organization_payload(slug: str) -> dict[str, Any]:
    return {
        "name": f"Clinic {slug}",
        "slug": slug,
        "depositPercent": 0.25,
        "adminEmail": f"admin@{slug}.example.com",
        "adminPassword": "correct-horse",
        "adminDisplayNameEn": "Dr. New Admin",
        "adminDisplayNameAr": "د. مدير جديد",
    }


async def _list_organizations(client: AsyncClient) -> list[dict[str, Any]]:
    response = await client.get("/api/v1/platform-admin/organizations")
    assert response.status_code == 200
    return response.json()["data"]


async def test_list_organizations_returns_seeded_tenant_with_pagination(
    platform_admin_client: AsyncClient,
) -> None:
    response = await platform_admin_client.get("/api/v1/platform-admin/organizations")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["pagination"]["total"] == 1
    organization = body["data"][0]
    assert organization["slug"] == "test-optometry"
    assert organization["adminEmail"] == "admin@lensora.test"
    assert organization["isActive"] is True


async def test_create_organization_provisions_tenant_and_its_admin_login(
    platform_admin_client: AsyncClient,
) -> None:
    response = await platform_admin_client.post(
        "/api/v1/platform-admin/organizations", json=_new_organization_payload("new-clinic")
    )

    assert response.status_code == 200
    created = response.json()["data"]
    assert created["slug"] == "new-clinic"
    assert created["adminEmail"] == "admin@new-clinic.example.com"
    assert created["isActive"] is True
    assert len(await _list_organizations(platform_admin_client)) == 2


async def test_create_organization_with_duplicate_slug_is_rejected(
    platform_admin_client: AsyncClient,
) -> None:
    payload = _new_organization_payload("test-optometry")
    response = await platform_admin_client.post(
        "/api/v1/platform-admin/organizations", json=payload
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "organization.slugTaken"


async def test_get_organization_returns_detail(platform_admin_client: AsyncClient) -> None:
    organizations = await _list_organizations(platform_admin_client)
    organization_id = organizations[0]["id"]

    response = await platform_admin_client.get(
        f"/api/v1/platform-admin/organizations/{organization_id}"
    )

    assert response.status_code == 200
    assert response.json()["data"]["id"] == organization_id


async def test_get_unknown_organization_returns_not_found(
    platform_admin_client: AsyncClient,
) -> None:
    response = await platform_admin_client.get(
        f"/api/v1/platform-admin/organizations/{uuid.uuid4()}"
    )

    assert response.status_code == 404


async def test_deactivate_then_activate_organization_persists_status(
    platform_admin_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    organizations = await _list_organizations(platform_admin_client)
    organization_id = organizations[0]["id"]

    deactivated = await platform_admin_client.patch(
        f"/api/v1/platform-admin/organizations/{organization_id}/status",
        json={"isActive": False},
    )

    assert deactivated.status_code == 200
    assert deactivated.json()["data"]["isActive"] is False
    async with db_sessionmaker() as session:
        stored = await session.get(Organization, uuid.UUID(organization_id))
        assert stored is not None and stored.is_active is False

    reactivated = await platform_admin_client.patch(
        f"/api/v1/platform-admin/organizations/{organization_id}/status",
        json={"isActive": True},
    )

    assert reactivated.status_code == 200
    assert reactivated.json()["data"]["isActive"] is True


async def test_set_status_for_unknown_organization_returns_not_found(
    platform_admin_client: AsyncClient,
) -> None:
    response = await platform_admin_client.patch(
        f"/api/v1/platform-admin/organizations/{uuid.uuid4()}/status",
        json={"isActive": False},
    )

    assert response.status_code == 404


async def test_dashboard_counts_reflect_organization_status(
    platform_admin_client: AsyncClient,
) -> None:
    await platform_admin_client.post(
        "/api/v1/platform-admin/organizations", json=_new_organization_payload("second-clinic")
    )
    organizations = await _list_organizations(platform_admin_client)
    await platform_admin_client.patch(
        f"/api/v1/platform-admin/organizations/{organizations[0]['id']}/status",
        json={"isActive": False},
    )

    response = await platform_admin_client.get("/api/v1/platform-admin/dashboard")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["totalOrganizations"] == 2
    assert data["activeOrganizations"] == 1
    assert data["inactiveOrganizations"] == 1
    assert data["organizationsCreatedThisMonth"] == 2


async def test_deactivating_one_organization_leaves_others_active(
    platform_admin_client: AsyncClient,
) -> None:
    await platform_admin_client.post(
        "/api/v1/platform-admin/organizations", json=_new_organization_payload("third-clinic")
    )
    organizations = await _list_organizations(platform_admin_client)
    target_id = organizations[0]["id"]

    await platform_admin_client.patch(
        f"/api/v1/platform-admin/organizations/{target_id}/status", json={"isActive": False}
    )

    organizations = await _list_organizations(platform_admin_client)
    statuses = {org["id"]: org["isActive"] for org in organizations}
    assert statuses[target_id] is False
    assert all(is_active for org_id, is_active in statuses.items() if org_id != target_id)


async def test_organization_admin_is_denied_every_platform_admin_route(
    tenant_admin_client: AsyncClient,
) -> None:
    organization_id = uuid.uuid4()
    responses = [
        await tenant_admin_client.get("/api/v1/platform-admin/organizations"),
        await tenant_admin_client.post(
            "/api/v1/platform-admin/organizations", json=_new_organization_payload("denied-clinic")
        ),
        await tenant_admin_client.get(f"/api/v1/platform-admin/organizations/{organization_id}"),
        await tenant_admin_client.patch(
            f"/api/v1/platform-admin/organizations/{organization_id}/status",
            json={"isActive": False},
        ),
        await tenant_admin_client.get("/api/v1/platform-admin/dashboard"),
    ]

    assert [response.status_code for response in responses] == [401] * len(responses)


async def test_platform_admin_routes_never_create_tenant_scoped_leakage(
    platform_admin_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    """Creating an organization seeds only that organization's catalog, never the caller's."""
    await platform_admin_client.post(
        "/api/v1/platform-admin/organizations", json=_new_organization_payload("isolated-clinic")
    )

    async with db_sessionmaker() as session:
        result = await session.execute(select(User).where(User.role == UserRole.ORGANIZATION_ADMIN))
        admins = list(result.scalars().all())

    assert {admin.email for admin in admins} == {
        "admin@lensora.test",
        "admin@isolated-clinic.example.com",
    }
    assert all(admin.organization_id is not None for admin in admins)
