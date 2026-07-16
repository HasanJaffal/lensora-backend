from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.exceptions import AccountEmailTakenError, OrganizationSlugTakenError
from app.core.security import verify_password
from app.db.seeds.organization_defaults import seed_lens_catalog, seed_tips
from app.features.auth.models import User, UserRole
from app.features.auth.repository import UserRepository
from app.features.lenses.models import LensType
from app.features.organizations.models import Organization
from app.features.organizations.repository import OrganizationRepository
from app.features.organizations.service import (
    OrganizationProvisioningRequest,
    OrganizationProvisioningService,
)
from app.features.tips.models import Tip
from app.management.provision_organization import provision_organization


def _request(*, org_slug: str, admin_email: str) -> OrganizationProvisioningRequest:
    return OrganizationProvisioningRequest(
        organization_name="Acme Optometry",
        organization_slug=org_slug,
        admin_email=admin_email,
        admin_password="correct-horse",
        admin_display_name_en="Dr. Jane Doe",
        admin_display_name_ar="د. جين دو",
        deposit_percent=Decimal("0.40"),
    )


async def _provision(
    session: AsyncSession, request: OrganizationProvisioningRequest
) -> tuple[Organization, User]:
    service = OrganizationProvisioningService(
        session, OrganizationRepository(session), UserRepository(session)
    )
    provisioned = await service.provision(request)
    return provisioned.organization, provisioned.admin_account


async def test_provision_creates_organization_and_admin_account(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    async with db_sessionmaker() as session, session.begin():
        organization, admin_account = await _provision(
            session, _request(org_slug="acme", admin_email="admin@acme.com")
        )

        assert organization.id is not None
        assert organization.slug == "acme"
        assert admin_account.organization_id == organization.id
        assert admin_account.role == UserRole.ORGANIZATION_ADMIN
        assert verify_password("correct-horse", admin_account.hashed_password)


async def test_provisioning_two_organizations_are_isolated_and_distinct(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    async with db_sessionmaker() as session, session.begin():
        org_a, admin_a = await _provision(
            session, _request(org_slug="org-a", admin_email="admin@org-a.com")
        )
        org_b, admin_b = await _provision(
            session, _request(org_slug="org-b", admin_email="admin@org-b.com")
        )

        assert org_a.id != org_b.id
        assert admin_a.organization_id != admin_b.organization_id


async def test_provision_with_duplicate_slug_is_rejected(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    async with db_sessionmaker() as session, session.begin():
        await _provision(session, _request(org_slug="acme", admin_email="first@acme.com"))

    async with db_sessionmaker() as session, session.begin():
        with pytest.raises(OrganizationSlugTakenError):
            await _provision(session, _request(org_slug="acme", admin_email="second@acme.com"))


async def test_provision_with_duplicate_admin_email_is_rejected(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    async with db_sessionmaker() as session, session.begin():
        await _provision(session, _request(org_slug="org-one", admin_email="admin@acme.com"))

    async with db_sessionmaker() as session, session.begin():
        with pytest.raises(AccountEmailTakenError):
            await _provision(session, _request(org_slug="org-two", admin_email="admin@acme.com"))


async def test_provisioning_seeds_lens_catalog_and_tips_per_organization(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    async def _count_for_org(model: type[LensType] | type[Tip], organization_id: object) -> int:
        async with db_sessionmaker() as session:
            result = await session.execute(
                select(func.count())
                .select_from(model)
                .where(model.organization_id == organization_id)
            )
            return result.scalar_one()

    acme = await provision_organization(
        _request(org_slug="acme", admin_email="admin@acme.com"), db_sessionmaker
    )
    acme_lens_type_count = await _count_for_org(LensType, acme.organization.id)
    acme_tip_count = await _count_for_org(Tip, acme.organization.id)

    assert acme_lens_type_count > 0
    assert acme_tip_count > 0

    other = await provision_organization(
        _request(org_slug="other-org", admin_email="other-admin@acme.com"), db_sessionmaker
    )

    assert await _count_for_org(LensType, other.organization.id) == acme_lens_type_count
    assert await _count_for_org(Tip, other.organization.id) == acme_tip_count
    assert await _count_for_org(LensType, acme.organization.id) == acme_lens_type_count

    async with db_sessionmaker() as session, session.begin():
        await seed_lens_catalog(session, acme.organization.id)
        await seed_tips(session, acme.organization.id)

    assert await _count_for_org(LensType, acme.organization.id) == acme_lens_type_count
    assert await _count_for_org(Tip, acme.organization.id) == acme_tip_count
