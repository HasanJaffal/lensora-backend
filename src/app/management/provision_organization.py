"""Provision an organization tenant and its single admin account.

Usage:
    python -m app.management.provision_organization \\
        --org-name "Acme Optometry" --org-slug acme \\
        --admin-email admin@acme.com --admin-password change-me \\
        --admin-display-name-en "Dr. Jane Doe" --admin-display-name-ar "د. جين دو"

Replaces the old ``SEED_DOCTOR_*`` env-seed path: every account now comes from an explicit,
auditable provisioning run rather than implicit startup seeding. Re-running with the same
org slug/admin email fails cleanly (each must be globally unique) rather than duplicating data;
the org's catalog/tips defaults are seeded idempotently by natural key, so a second run against
an already-provisioned organization only fills in whatever defaults are still missing.
"""

import argparse
import asyncio
import sys
from decimal import Decimal, InvalidOperation

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.exceptions import AppError
from app.db.engine import get_sessionmaker
from app.db.seeds.organization_defaults import seed_lens_catalog, seed_tips
from app.features.auth.repository import UserRepository
from app.features.organizations.repository import OrganizationRepository
from app.features.organizations.service import (
    OrganizationProvisioningRequest,
    OrganizationProvisioningService,
    ProvisionedOrganization,
)

DEFAULT_DEPOSIT_PERCENT = Decimal("0.40")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision an organization tenant and its single ORGANIZATION_ADMIN account."
    )
    parser.add_argument("--org-name", required=True, help="Organization display name")
    parser.add_argument("--org-slug", required=True, help="Organization slug (globally unique)")
    parser.add_argument("--admin-email", required=True, help="Admin account login email")
    parser.add_argument("--admin-password", required=True, help="Admin account password")
    parser.add_argument("--admin-display-name-en", required=True)
    parser.add_argument("--admin-display-name-ar", required=True)
    parser.add_argument(
        "--deposit-percent",
        default=str(DEFAULT_DEPOSIT_PERCENT),
        help=f"Lens-order deposit fraction for this org (default: {DEFAULT_DEPOSIT_PERCENT})",
    )
    return parser.parse_args(argv)


async def provision_organization(
    request: OrganizationProvisioningRequest,
    sessionmaker: async_sessionmaker[AsyncSession] | None = None,
) -> ProvisionedOrganization:
    sessionmaker = sessionmaker or get_sessionmaker()
    async with sessionmaker() as session, session.begin():
        service = OrganizationProvisioningService(
            session, OrganizationRepository(session), UserRepository(session)
        )
        provisioned = await service.provision(request)
        organization_id = provisioned.organization.id
        await seed_lens_catalog(session, organization_id)
        await seed_tips(session, organization_id)
        return provisioned


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        deposit_percent = Decimal(args.deposit_percent)
    except InvalidOperation:
        print(f"Invalid --deposit-percent value: {args.deposit_percent!r}", file=sys.stderr)
        raise SystemExit(1) from None

    request = OrganizationProvisioningRequest(
        organization_name=args.org_name,
        organization_slug=args.org_slug,
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        admin_display_name_en=args.admin_display_name_en,
        admin_display_name_ar=args.admin_display_name_ar,
        deposit_percent=deposit_percent,
    )

    try:
        provisioned = asyncio.run(provision_organization(request))
    except AppError as error:
        print(f"Provisioning failed: {error.message}", file=sys.stderr)
        raise SystemExit(1) from None

    print(
        f"Provisioned organization '{provisioned.organization.name}' "
        f"(slug={provisioned.organization.slug}, id={provisioned.organization.id}) "
        f"with admin account {provisioned.admin_account.email}"
    )


if __name__ == "__main__":
    main()
