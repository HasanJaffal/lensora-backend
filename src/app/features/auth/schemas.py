from pydantic import EmailStr, Field

from app.common.schema import CamelModel
from app.features.auth.models import User
from app.features.organizations.models import Organization


class OrganizationSummaryDto(CamelModel):
    id: str
    name: str
    slug: str

    @classmethod
    def from_model(cls, organization: Organization) -> "OrganizationSummaryDto":
        return cls(id=str(organization.id), name=organization.name, slug=organization.slug)


class UserDto(CamelModel):
    id: str
    email: str
    display_name_en: str
    display_name_ar: str
    role: str
    organization: OrganizationSummaryDto | None

    @classmethod
    def from_model(cls, user: User, organization: Organization | None) -> "UserDto":
        return cls(
            id=str(user.id),
            email=user.email,
            display_name_en=user.display_name_en,
            display_name_ar=user.display_name_ar,
            role=user.role,
            organization=(
                OrganizationSummaryDto.from_model(organization)
                if organization is not None
                else None
            ),
        )


class LoginRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(CamelModel):
    access_token: str
    user: UserDto
