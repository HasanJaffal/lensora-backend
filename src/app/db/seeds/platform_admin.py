"""The single PLATFORM_ADMIN account, seeded from the environment at application startup.

The environment is the source of truth for these credentials: there is no self-registration
and no in-app account creation, so every boot re-applies the configured values rather than
leaving a stale password behind. Seeding is skipped when no credentials are configured.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.exceptions import AccountEmailTakenError
from app.core.config import Settings
from app.core.security import hash_password
from app.db.engine import get_sessionmaker
from app.features.auth.models import User, UserRole
from app.features.auth.repository import UserRepository


@dataclass(frozen=True)
class PlatformAdminCredentials:
    email: str
    password: str
    display_name_en: str
    display_name_ar: str


def resolve_platform_admin_credentials(settings: Settings) -> PlatformAdminCredentials | None:
    if not settings.platform_admin_email or not settings.platform_admin_password:
        return None
    return PlatformAdminCredentials(
        email=settings.platform_admin_email,
        password=settings.platform_admin_password,
        display_name_en=settings.platform_admin_display_name_en,
        display_name_ar=settings.platform_admin_display_name_ar,
    )


async def seed_platform_admin(session: AsyncSession, credentials: PlatformAdminCredentials) -> User:
    users = UserRepository(session)
    account_with_email = await users.get_by_email(credentials.email)
    if account_with_email is not None and account_with_email.role != UserRole.PLATFORM_ADMIN:
        raise AccountEmailTakenError(
            f"PLATFORM_ADMIN_EMAIL '{credentials.email}' already belongs to an organization account"
        )

    admin = account_with_email or await users.get_platform_admin()
    if admin is None:
        admin = User(
            organization_id=None,
            email=credentials.email,
            hashed_password=hash_password(credentials.password),
            display_name_en=credentials.display_name_en,
            display_name_ar=credentials.display_name_ar,
            role=UserRole.PLATFORM_ADMIN,
        )
        users.add(admin)
        await session.flush()
        return admin

    admin.email = credentials.email
    admin.hashed_password = hash_password(credentials.password)
    admin.display_name_en = credentials.display_name_en
    admin.display_name_ar = credentials.display_name_ar
    admin.is_active = True
    return admin


async def seed_platform_admin_from_settings(
    settings: Settings,
    sessionmaker: async_sessionmaker[AsyncSession] | None = None,
) -> User | None:
    credentials = resolve_platform_admin_credentials(settings)
    if credentials is None:
        return None
    async with (sessionmaker or get_sessionmaker())() as session, session.begin():
        return await seed_platform_admin(session, credentials)
