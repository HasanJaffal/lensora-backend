import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.exceptions import AccountEmailTakenError
from app.core.config import Settings
from app.core.security import verify_password
from app.db.seeds.platform_admin import (
    PlatformAdminCredentials,
    resolve_platform_admin_credentials,
    seed_platform_admin,
)
from app.features.auth.models import User, UserRole

CONFIGURED_CREDENTIALS = PlatformAdminCredentials(
    email="platform-admin@lensora.dev",
    password="configured-password",
    display_name_en="Platform Admin",
    display_name_ar="مسؤول المنصة",
)


async def _seed(
    sessionmaker: async_sessionmaker[AsyncSession], credentials: PlatformAdminCredentials
) -> None:
    async with sessionmaker() as session, session.begin():
        await seed_platform_admin(session, credentials)


async def _platform_admins(sessionmaker: async_sessionmaker[AsyncSession]) -> list[User]:
    async with sessionmaker() as session:
        result = await session.execute(
            select(User).where(User.role == UserRole.PLATFORM_ADMIN).order_by(User.email)
        )
        return list(result.scalars().all())


async def test_seeds_the_platform_admin_when_none_exists(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(db_sessionmaker, CONFIGURED_CREDENTIALS)

    admins = await _platform_admins(db_sessionmaker)
    assert len(admins) == 1
    assert admins[0].email == CONFIGURED_CREDENTIALS.email
    assert admins[0].organization_id is None
    assert verify_password(CONFIGURED_CREDENTIALS.password, admins[0].hashed_password)


async def test_reapplies_the_configured_password_without_duplicating_the_account(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(db_sessionmaker, CONFIGURED_CREDENTIALS)
    rotated = PlatformAdminCredentials(
        email=CONFIGURED_CREDENTIALS.email,
        password="rotated-password",
        display_name_en=CONFIGURED_CREDENTIALS.display_name_en,
        display_name_ar=CONFIGURED_CREDENTIALS.display_name_ar,
    )

    await _seed(db_sessionmaker, rotated)

    admins = await _platform_admins(db_sessionmaker)
    assert len(admins) == 1
    assert verify_password(rotated.password, admins[0].hashed_password)


async def test_moves_the_existing_platform_admin_to_the_newly_configured_email(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(db_sessionmaker, CONFIGURED_CREDENTIALS)
    relocated = PlatformAdminCredentials(
        email="successor@lensora.dev",
        password=CONFIGURED_CREDENTIALS.password,
        display_name_en=CONFIGURED_CREDENTIALS.display_name_en,
        display_name_ar=CONFIGURED_CREDENTIALS.display_name_ar,
    )

    await _seed(db_sessionmaker, relocated)

    admins = await _platform_admins(db_sessionmaker)
    assert len(admins) == 1
    assert admins[0].email == relocated.email


async def test_rejects_an_email_already_owned_by_an_organization_account(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    collides_with_tenant_admin = PlatformAdminCredentials(
        email="admin@lensora.test",  # the organization admin conftest provisions
        password=CONFIGURED_CREDENTIALS.password,
        display_name_en=CONFIGURED_CREDENTIALS.display_name_en,
        display_name_ar=CONFIGURED_CREDENTIALS.display_name_ar,
    )

    with pytest.raises(AccountEmailTakenError):
        await _seed(db_sessionmaker, collides_with_tenant_admin)

    assert await _platform_admins(db_sessionmaker) == []


def test_credentials_resolve_from_the_environment() -> None:
    settings = Settings(
        PLATFORM_ADMIN_EMAIL="platform-admin@lensora.dev",
        PLATFORM_ADMIN_PASSWORD="configured-password",
        PLATFORM_ADMIN_DISPLAY_NAME_EN="Platform Admin",
        PLATFORM_ADMIN_DISPLAY_NAME_AR="مسؤول المنصة",
    )

    assert resolve_platform_admin_credentials(settings) == CONFIGURED_CREDENTIALS


@pytest.mark.parametrize(
    ("email", "password"),
    [(None, "configured-password"), ("platform-admin@lensora.dev", None), (None, None)],
)
def test_no_credentials_resolve_when_the_environment_is_incomplete(
    email: str | None, password: str | None
) -> None:
    settings = Settings(PLATFORM_ADMIN_EMAIL=email, PLATFORM_ADMIN_PASSWORD=password)

    assert resolve_platform_admin_credentials(settings) is None


@pytest.mark.parametrize("reserved_email", ["admin@lensora.local", "admin@lensora.test"])
def test_an_unroutable_email_is_rejected_before_the_account_is_seeded(reserved_email: str) -> None:
    """Reserved TLDs pass argon2 hashing but fail EmailStr at /auth/login, stranding the account."""
    with pytest.raises(ValidationError):
        Settings(PLATFORM_ADMIN_EMAIL=reserved_email, PLATFORM_ADMIN_PASSWORD="configured-password")
