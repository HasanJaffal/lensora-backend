from decimal import Decimal

from app.common.schema import CamelModel
from app.features.organizations.models import Organization


class OrganizationDto(CamelModel):
    id: str
    name: str
    slug: str
    deposit_percent: Decimal

    @classmethod
    def from_model(cls, organization: Organization) -> "OrganizationDto":
        return cls(
            id=str(organization.id),
            name=organization.name,
            slug=organization.slug,
            deposit_percent=organization.deposit_percent,
        )
