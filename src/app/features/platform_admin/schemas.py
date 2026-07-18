from datetime import datetime
from decimal import Decimal

from pydantic import EmailStr, Field

from app.common.schema import CamelModel
from app.features.auth.models import User
from app.features.organizations.models import Organization


class OrganizationDto(CamelModel):
    id: str
    name: str
    slug: str
    deposit_percent: Decimal
    admin_email: str
    admin_display_name_en: str
    admin_display_name_ar: str
    created_at: datetime

    @classmethod
    def from_models(cls, organization: Organization, admin: User) -> "OrganizationDto":
        return cls(
            id=str(organization.id),
            name=organization.name,
            slug=organization.slug,
            deposit_percent=organization.deposit_percent,
            admin_email=admin.email,
            admin_display_name_en=admin.display_name_en,
            admin_display_name_ar=admin.display_name_ar,
            created_at=organization.created_at,
        )


class CreateOrganizationRequest(CamelModel):
    name: str = Field(min_length=1)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    deposit_percent: Decimal = Field(ge=0, le=1)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8)
    admin_display_name_en: str = Field(min_length=1)
    admin_display_name_ar: str = Field(min_length=1)
