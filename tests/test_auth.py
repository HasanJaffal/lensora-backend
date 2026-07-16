import uuid
from collections.abc import AsyncIterator

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.common.deps import get_auth_service
from app.core.security import create_access_token, hash_password
from app.features.auth.models import User, UserRole
from app.features.auth.repository import UserRepository
from app.features.auth.service import AuthService
from app.main import create_app

DOCTOR_PASSWORD = "correct-horse"


def _make_doctor(*, is_active: bool = True) -> User:
    user = User(
        id=uuid.uuid4(),
        email="doctor@lensora.com",
        hashed_password=hash_password(DOCTOR_PASSWORD),
        display_name_en="Dr. Jane Doe",
        display_name_ar="د. جين دو",
        role=UserRole.OPTOMETRIST,
        is_active=is_active,
    )
    return user


class _InMemoryUserRepository(UserRepository):
    def __init__(self, users: list[User]) -> None:
        self._users = users

    async def get_by_email(self, email: str) -> User | None:
        return next((user for user in self._users if user.email == email), None)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return next((user for user in self._users if user.id == user_id), None)


def _client_for(users: list[User]) -> tuple[FastAPI, User]:
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: AuthService(
        _InMemoryUserRepository(users)
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
    assert body["data"]["user"]["role"] == "optometrist"


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

    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(doctor.id)


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
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth.sessionExpired"


async def test_me_for_deleted_user_returns_session_expired(
    auth_client: tuple[AsyncClient, User],
) -> None:
    client, _ = auth_client
    token = create_access_token(str(uuid.uuid4()))
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )

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
