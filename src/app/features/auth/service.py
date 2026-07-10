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


class AuthService:
    """Authentication business logic: credential checks and token resolution."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def authenticate(self, email: str, password: str) -> tuple[str, User]:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")
        self._ensure_active(user)
        return create_access_token(str(user.id)), user

    async def resolve_token(self, token: str) -> User:
        try:
            subject = decode_access_token(token)
            user_id = uuid.UUID(subject)
        except (TokenError, ValueError) as exc:
            raise SessionExpiredError("Session has expired") from exc

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise SessionExpiredError("Session has expired")
        self._ensure_active(user)
        return user

    @staticmethod
    def _ensure_active(user: User) -> None:
        if not user.is_active:
            raise AccountDisabledError("Account is disabled")
