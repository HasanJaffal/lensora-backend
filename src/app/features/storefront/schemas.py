from decimal import Decimal

from app.common.schema import CamelModel
from app.features.inventory.models import InventoryCategory, InventoryItem
from app.features.organizations.models import Organization

PUBLIC_CATEGORIES: tuple[InventoryCategory, ...] = (
    InventoryCategory.FRAME,
    InventoryCategory.SUN,
)


class PublicOrganizationDto(CamelModel):
    """The only organization fields an anonymous visitor may see (FR-STORE-7)."""

    name: str
    slug: str

    @classmethod
    def from_model(cls, organization: Organization) -> "PublicOrganizationDto":
        return cls(name=organization.name, slug=organization.slug)


class PublicProductDto(CamelModel):
    """Storefront-safe projection of an inventory item.

    Deliberately omits `sku`, `qty`, `threshold`, and derived stock ratios: those are
    internal stock-management detail and must never reach the public surface (FR-STORE-7).
    """

    id: str
    category: str
    name: str
    brand: str
    spec: str
    shape: str | None
    color: str | None
    price: Decimal

    @classmethod
    def from_model(cls, item: InventoryItem) -> "PublicProductDto":
        return cls(
            id=str(item.id),
            category=item.category,
            name=item.name,
            brand=item.brand,
            spec=item.spec,
            shape=item.shape,
            color=item.color,
            price=item.price,
        )
