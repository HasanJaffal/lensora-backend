from pydantic import EmailStr, Field

from app.common.schema import CamelModel
from app.features.auth.models import User


class UserDto(CamelModel):
    id: str
    email: str
    display_name_en: str
    display_name_ar: str
    role: str

    @classmethod
    def from_model(cls, user: User) -> "UserDto":
        return cls(
            id=str(user.id),
            email=user.email,
            display_name_en=user.display_name_en,
            display_name_ar=user.display_name_ar,
            role=user.role,
        )


class LoginRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(CamelModel):
    access_token: str
    user: UserDto
