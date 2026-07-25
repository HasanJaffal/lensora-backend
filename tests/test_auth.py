import uuid
from collections.abc import AsyncIterator
from decimal import Decimal

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.common.deps import get_auth_service
from app.core.security import create_access_token, hash_password
from app.features.auth.models import User, UserRole
from app.features.auth.repository import UserRepository
from app.features.auth.service import AuthService
from app.features.organizations.models import Organization
from app.features.organizations.repository import OrganizationRepository
from app.main import create_app

DOCTOR_PASSWORD = "correct-horse"


def _make_doctor(*, is_active: bool = True) -> User:
    user = User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        email="doctor@lensora.com",
        hashed_password=hash_password(DOCTOR_PASSWORD),
        display_name_en="Dr. Jane Doe",
        display_name_ar="د. جين دو",
        role=UserRole.ORGANIZATION_ADMIN,
        is_active=is_active,
    )
    return user


def _make_platform_admin() -> User:
    return User(
        id=uuid.uuid4(),
        organization_id=None,
        email="platform@lensora.com",
        hashed_password=hash_password(DOCTOR_PASSWORD),
        display_name_en="Platform Owner",
        display_name_ar="مالك المنصة",
        role=UserRole.PLATFORM_ADMIN,
        is_active=True,
    )


def _make_organization(organization_id: uuid.UUID, *, is_active: bool = True) -> Organization:
    return Organization(
        id=organization_id,
        name="Lensora Optics",
        slug="lensora-optics",
        deposit_percent=Decimal("0.2000"),
        is_active=is_active,
    )


class _InMemoryUserRepository(UserRepository):
    def __init__(self, users: list[User]) -> None:
        self._users = users

    async def get_by_email(self, email: str) -> User | None:
        return next((user for user in self._users if user.email == email), None)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return next((user for user in self._users if user.id == user_id), None)


class _InMemoryOrganizationRepository(OrganizationRepository):
    def __init__(self, organizations: list[Organization]) -> None:
        self._organizations = organizations

    async def get_by_id(self, organization_id: uuid.UUID) -> Organization | None:
        return next((org for org in self._organizations if org.id == organization_id), None)


def _client_for(users: list[User], *, organization_is_active: bool = True) -> tuple[FastAPI, User]:
    app = create_app()
    organizations = [
        _make_organization(user.organization_id, is_active=organization_is_active)
        for user in users
        if user.organization_id is not None
    ]
    app.dependency_overrides[get_auth_service] = lambda: AuthService(
        _InMemoryUserRepository(users), _InMemoryOrganizationRepository(organizations)
    )
    return app, users[0]


@pytest_asyncio.fixture
async def doctor() -> User:
    return _make_doctor()


@pytest_asyncio.fixture
async def auth_client(doctor: User) -> AsyncIterator[tuple[AsyncClient, User]]:
    app, seeded = _client_for([doctor])
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client, seeded


async def test_login_returns_token_and_user(
    auth_client: tuple[AsyncClient, User],
) -> None:
    client, doctor = auth_client
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": doctor.email, "password": DOCTOR_PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["accessToken"]
    assert body["data"]["user"]["email"] == doctor.email
    assert body["data"]["user"]["displayNameAr"] == doctor.display_name_ar
    assert body["data"]["user"]["role"] == "organizationAdmin"
    assert body["data"]["user"]["organization"]["id"] == str(doctor.organization_id)
    assert body["data"]["user"]["organization"]["slug"] == "lensora-optics"


async def test_login_with_wrong_password_returns_invalid_credentials(
    auth_client: tuple[AsyncClient, User],
) -> None:
    client, doctor = auth_client
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": doctor.email, "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.invalidCredentials"


async def test_login_with_unknown_email_returns_invalid_credentials(
    auth_client: tuple[AsyncClient, User],
) -> None:
    client, _ = auth_client
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@lensora.com", "password": DOCTOR_PASSWORD},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.invalidCredentials"


async def test_login_with_invalid_email_returns_validation_error(
    auth_client: tuple[AsyncClient, User],
) -> None:
    client, _ = auth_client
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": DOCTOR_PASSWORD},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def test_me_with_valid_token_returns_current_user(
    auth_client: tuple[AsyncClient, User],
) -> None:
    client, doctor = auth_client
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": doctor.email, "password": DOCTOR_PASSWORD},
    )
    token = login.json()["data"]["accessToken"]

    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["id"] == str(doctor.id)
    assert body["organization"]["id"] == str(doctor.organization_id)


async def test_me_without_token_returns_session_expired(
    auth_client: tuple[AsyncClient, User],
) -> None:
    client, _ = auth_client
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.sessionExpired"


async def test_me_with_malformed_token_returns_session_expired(
    auth_client: tuple[AsyncClient, User],
) -> None:
    client, _ = auth_client
    response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.sessionExpired"


async def test_me_for_deleted_user_returns_session_expired(
    auth_client: tuple[AsyncClient, User],
) -> None:
    client, _ = auth_client
    token = create_access_token(str(uuid.uuid4()))
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.sessionExpired"


async def test_login_for_disabled_account_returns_account_disabled() -> None:
    disabled_doctor = _make_doctor(is_active=False)
    app, _ = _client_for([disabled_doctor])
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": disabled_doctor.email, "password": DOCTOR_PASSWORD},
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "auth.accountDisabled"


async def test_login_for_deactivated_organization_is_rejected() -> None:
    doctor = _make_doctor()
    app, _ = _client_for([doctor], organization_is_active=False)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": doctor.email, "password": DOCTOR_PASSWORD},
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "organization.deactivated"


async def test_existing_session_is_revoked_when_organization_is_deactivated() -> None:
    doctor = _make_doctor()
    app, _ = _client_for([doctor], organization_is_active=False)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    token = create_access_token(str(doctor.id))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "organization.deactivated"


async def test_platform_admin_login_is_unaffected_by_organization_status() -> None:
    platform_admin = _make_platform_admin()
    app, _ = _client_for([platform_admin], organization_is_active=False)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": platform_admin.email, "password": DOCTOR_PASSWORD},
        )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["user"]["role"] == "platformAdmin"
    assert body["user"]["organization"] is None


async def test_logout_acknowledges_for_authenticated_user(
    auth_client: tuple[AsyncClient, User],
) -> None:
    client, doctor = auth_client
    token = create_access_token(str(doctor.id))
    response = await client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
