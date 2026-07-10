from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import SessionExpiredError
from app.db.session import get_session
from app.features.auth.models import User
from app.features.auth.repository import UserRepository
from app.features.auth.service import AuthService

_bearer_scheme = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(UserRepository(session))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    service: AuthServiceDep,
) -> User:
    if credentials is None:
        raise SessionExpiredError("Session has expired")
    return await service.resolve_token(credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_auth(_: CurrentUser) -> None:
    """Router-level guard: use in ``APIRouter(dependencies=[Depends(require_auth)])``."""
