import uuid

from app.common.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
    SessionExpiredError,
)
from app.core.security import (
    TokenError,
    create_access_token,
    decode_access_token,
    verify_password,
)
from app.features.auth.models import User
from app.features.auth.repository import UserRepository
from app.features.organizations.models import Organization
from app.features.organizations.repository import OrganizationRepository


class AuthService:
    """Authentication business logic: credential checks and token resolution."""

    def __init__(self, users: UserRepository, organizations: OrganizationRepository) -> None:
        self._users = users
        self._organizations = organizations

    async def authenticate(
        self, email: str, password: str
    ) -> tuple[str, User, Organization | None]:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")
        self._ensure_active(user)
        organization = await self.get_organization_for(user)
        return create_access_token(str(user.id)), user, organization

    async def resolve_token(self, token: str) -> tuple[User, Organization | None]:
        try:
            subject = decode_access_token(token)
            user_id = uuid.UUID(subject)
        except (TokenError, ValueError) as exc:
            raise SessionExpiredError("Session has expired") from exc

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise SessionExpiredError("Session has expired")
        self._ensure_active(user)
        organization = await self.get_organization_for(user)
        return user, organization

    async def get_organization_for(self, user: User) -> Organization | None:
        if user.organization_id is None:
            return None
        organization = await self._organizations.get_by_id(user.organization_id)
        if organization is None:
            raise SessionExpiredError("Session has expired")
        return organization

    @staticmethod
    def _ensure_active(user: User) -> None:
        if not user.is_active:
            raise AccountDisabledError("Account is disabled")
