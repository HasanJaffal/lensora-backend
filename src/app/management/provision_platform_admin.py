"""Provision the single PLATFORM_ADMIN account.

Usage:
    python -m app.management.provision_platform_admin \\
        --email admin@lensora.example --password change-me \\
        --display-name-en "Platform Admin" --display-name-ar "مسؤول المنصة"

Platform admins are created by developers with server/DB access, the same posture as
``provision_organization`` for tenant admins — there is no self-registration, no in-app
creation of additional platform admins, and no env-var seeding at app startup. Re-running with
an email that already exists fails cleanly (``auth.emailTaken``) rather than duplicating or
resetting the account; rotate a password by re-running with ``--rotate-password`` instead.
"""

import argparse
import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.exceptions import AccountEmailTakenError, AppError
from app.core.security import hash_password
from app.db import registry as db_registry  # noqa: F401 - import registers audit listeners
from app.db.engine import get_sessionmaker
from app.features.auth.models import User, UserRole
from app.features.auth.repository import UserRepository


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Provision or rotate the PLATFORM_ADMIN account.")
    parser.add_argument("--email", required=True, help="Platform admin login email")
    parser.add_argument("--password", required=True, help="Platform admin password")
    parser.add_argument("--display-name-en", required=True)
    parser.add_argument("--display-name-ar", required=True)
    parser.add_argument(
        "--rotate-password",
        action="store_true",
        help="If the account already exists, update its password instead of failing",
    )
    return parser.parse_args(argv)


async def provision_platform_admin(
    *,
    email: str,
    password: str,
    display_name_en: str,
    display_name_ar: str,
    rotate_password: bool,
    sessionmaker: async_sessionmaker[AsyncSession] | None = None,
) -> User:
    sessionmaker = sessionmaker or get_sessionmaker()
    async with sessionmaker() as session, session.begin():
        users = UserRepository(session)
        existing = await users.get_by_email(email)

        if existing is not None:
            if not rotate_password:
                raise AccountEmailTakenError(f"Account email '{email}' is already in use")
            existing.hashed_password = hash_password(password)
            existing.display_name_en = display_name_en
            existing.display_name_ar = display_name_ar
            return existing

        admin = User(
            organization_id=None,
            email=email,
            hashed_password=hash_password(password),
            display_name_en=display_name_en,
            display_name_ar=display_name_ar,
            role=UserRole.PLATFORM_ADMIN,
        )
        users.add(admin)
        await session.flush()
        return admin


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    try:
        admin = asyncio.run(
            provision_platform_admin(
                email=args.email,
                password=args.password,
                display_name_en=args.display_name_en,
                display_name_ar=args.display_name_ar,
                rotate_password=args.rotate_password,
            )
        )
    except AppError as error:
        print(f"Provisioning failed: {error.message}", file=sys.stderr)
        raise SystemExit(1) from None

    print(f"Platform admin ready: {admin.email} (id={admin.id})")


if __name__ == "__main__":
    main()
