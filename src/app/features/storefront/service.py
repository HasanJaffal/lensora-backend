from app.common.exceptions import NotFoundError, ValidationError
from app.features.inventory.models import InventoryCategory
from app.features.organizations.models import Organization
from app.features.organizations.repository import OrganizationRepository
from app.features.storefront.repository import StorefrontProductRepository
from app.features.storefront.schemas import (
    PUBLIC_CATEGORIES,
    PublicOrganizationDto,
    PublicProductDto,
)


class StorefrontService:
    """Public, unauthenticated read access to one organization's storefront."""

    def __init__(
        self,
        organizations: OrganizationRepository,
        products: StorefrontProductRepository,
    ) -> None:
        self._organizations = organizations
        self._products = products

    async def get_public_organization(self, slug: str) -> PublicOrganizationDto:
        return PublicOrganizationDto.from_model(await self._require_visible_organization(slug))

    async def list_public_products(
        self, slug: str, category: InventoryCategory | None
    ) -> list[PublicProductDto]:
        organization = await self._require_visible_organization(slug)
        items = await self._products.list_public_products(
            organization_id=organization.id, category=category
        )
        return [PublicProductDto.from_model(item) for item in items]

    async def _require_visible_organization(self, slug: str) -> Organization:
        """Collapse "no such slug" and "deactivated" into one indistinguishable outcome.

        A visitor must not be able to tell a suspended tenant from one that never existed,
        mirroring the cross-tenant posture of FR-TENANT-4 / NFR-0 (FR-STORE-6).
        """
        organization = await self._organizations.get_by_slug(slug)
        if organization is None or not organization.is_active:
            raise NotFoundError(f"Storefront '{slug}' not found")
        return organization


def parse_public_category(category: str | None) -> InventoryCategory | None:
    """Reject any category outside the public catalog rather than silently ignoring it."""
    if category is None:
        return None
    allowed = ", ".join(member.value for member in PUBLIC_CATEGORIES)
    try:
        parsed = InventoryCategory(category)
    except ValueError as exc:
        raise ValidationError(
            f"Unknown category '{category}'; expected one of: {allowed}"
        ) from exc
    if parsed not in PUBLIC_CATEGORIES:
        raise ValidationError(f"Category '{category}' is not public; expected one of: {allowed}")
    return parsed
