"""Public storefront tests (FR-STORE).

Every request here is made with the ``anonymous_client`` — no principal, no Authorization
header — which is the point: the storefront is the one surface that must work without an
account, while still never exposing another organization's data or any internal detail.
"""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.inventory.models import InventoryItem
from app.features.organizations.models import Organization
from tests.conftest import ProvisionedTenant

_INTERNAL_PRODUCT_FIELDS = ("sku", "qty", "threshold", "quantityRatio", "status")


async def _deactivate(sessionmaker: async_sessionmaker[AsyncSession], slug: str) -> None:
    async with sessionmaker() as session, session.begin():
        result = await session.execute(select(Organization).where(Organization.slug == slug))
        result.scalar_one().is_active = False


async def test_storefront_returns_public_organization_without_authentication(
    anonymous_client: AsyncClient,
) -> None:
    response = await anonymous_client.get("/api/v1/storefront/org-a")

    assert response.status_code == 200
    assert response.json()["data"] == {"name": "Org A Optometry", "slug": "org-a"}


async def test_storefront_never_exposes_internal_organization_fields(
    anonymous_client: AsyncClient,
) -> None:
    response = await anonymous_client.get("/api/v1/storefront/org-a")

    data = response.json()["data"]
    for internal_field in ("id", "depositPercent", "isActive", "createdAt", "adminEmail"):
        assert internal_field not in data


async def test_unknown_slug_is_not_found(anonymous_client: AsyncClient) -> None:
    response = await anonymous_client.get("/api/v1/storefront/no-such-practice")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_deactivated_organization_is_indistinguishable_from_a_missing_one(
    anonymous_client: AsyncClient,
    two_org_db_sessionmaker: tuple[
        async_sessionmaker[AsyncSession], ProvisionedTenant, ProvisionedTenant
    ],
) -> None:
    """A visitor must not be able to tell a suspended tenant from one that never existed."""
    sessionmaker, _org_a, _org_b = two_org_db_sessionmaker
    await _deactivate(sessionmaker, "org-a")

    deactivated = await anonymous_client.get("/api/v1/storefront/org-a")
    missing = await anonymous_client.get("/api/v1/storefront/definitely-not-a-tenant")

    assert deactivated.status_code == missing.status_code == 404
    assert deactivated.json()["error"]["code"] == missing.json()["error"]["code"]


async def test_deactivated_organization_hides_its_products(
    anonymous_client: AsyncClient,
    two_org_db_sessionmaker: tuple[
        async_sessionmaker[AsyncSession], ProvisionedTenant, ProvisionedTenant
    ],
) -> None:
    sessionmaker, _org_a, _org_b = two_org_db_sessionmaker
    await _deactivate(sessionmaker, "org-a")

    response = await anonymous_client.get("/api/v1/storefront/org-a/products")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource.notFound"


async def test_products_are_limited_to_public_categories_and_in_stock_items(
    anonymous_client: AsyncClient,
) -> None:
    response = await anonymous_client.get("/api/v1/storefront/org-a/products")

    assert response.status_code == 200
    products = response.json()["data"]
    assert products
    assert {product["category"] for product in products} == {"frame", "sun"}


async def test_products_never_expose_internal_stock_detail(
    anonymous_client: AsyncClient,
) -> None:
    response = await anonymous_client.get("/api/v1/storefront/org-a/products")

    for product in response.json()["data"]:
        for internal_field in _INTERNAL_PRODUCT_FIELDS:
            assert internal_field not in product


async def test_products_can_be_filtered_by_public_category(
    anonymous_client: AsyncClient,
) -> None:
    for category in ("frame", "sun"):
        response = await anonymous_client.get(
            "/api/v1/storefront/org-a/products", params={"category": category}
        )

        assert response.status_code == 200
        products = response.json()["data"]
        assert products
        assert {product["category"] for product in products} == {category}


async def test_non_public_categories_are_rejected(anonymous_client: AsyncClient) -> None:
    """Clinical/consumable stock must not be reachable, even by explicit request."""
    for category in ("lens", "contact", "solution", "care"):
        response = await anonymous_client.get(
            "/api/v1/storefront/org-a/products", params={"category": category}
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation.error"


async def test_unknown_category_is_rejected(anonymous_client: AsyncClient) -> None:
    response = await anonymous_client.get(
        "/api/v1/storefront/org-a/products", params={"category": "telescopes"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation.error"


async def test_storefront_only_serves_the_requested_organizations_products(
    anonymous_client: AsyncClient,
    two_org_db_sessionmaker: tuple[
        async_sessionmaker[AsyncSession], ProvisionedTenant, ProvisionedTenant
    ],
) -> None:
    """The slug is the only tenant boundary here, so it must scope reads absolutely."""
    sessionmaker, org_a, _org_b = two_org_db_sessionmaker

    response = await anonymous_client.get("/api/v1/storefront/org-a/products")

    returned_ids = {product["id"] for product in response.json()["data"]}
    async with sessionmaker() as session:
        result = await session.execute(
            select(InventoryItem.id).where(
                InventoryItem.organization_id == org_a.organization.id
            )
        )
        org_a_ids = {str(item_id) for item_id in result.scalars().all()}

    assert returned_ids
    assert returned_ids <= org_a_ids
