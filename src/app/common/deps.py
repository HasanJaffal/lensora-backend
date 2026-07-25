from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.common.exceptions import UnauthorizedError
from app.common.tenant_context import TenantContext, tenant_context
from app.db.engine import get_sessionmaker
from app.db.session import get_session
from app.features.auth.models import User, UserRole
from app.features.auth.repository import UserRepository
from app.features.auth.service import AuthService
from app.features.organizations.repository import OrganizationRepository

_bearer_scheme = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_uow_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Sessionmaker used by services that own their own transaction boundary (Unit of Work).

    Exposed as a dependency so tests can bind Unit-of-Work writes to an isolated engine.
    """
    return get_sessionmaker()


UowSessionmakerDep = Annotated[async_sessionmaker[AsyncSession], Depends(get_uow_sessionmaker)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(UserRepository(session), OrganizationRepository(session))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    service: AuthServiceDep,
) -> User:
    if credentials is None:
        raise UnauthorizedError("Authentication credentials were not provided")
    user, _ = await service.resolve_token(credentials.credentials)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_auth(_: CurrentUser) -> None:
    """Router-level guard: use in ``APIRouter(dependencies=[Depends(require_auth)])``."""


async def get_tenant_context(current_user: CurrentUser) -> AsyncIterator[TenantContext]:
    """Bind a ``TenantContext`` derived from the authenticated account for the request lifetime.

    Rejects ``PLATFORM_ADMIN`` principals outright: they have no ``organization_id`` and must
    never be scoped to a tenant.

    Must be an async generator: FastAPI runs sync dependencies in a threadpool, where each
    call into the generator can land on a different thread and break ``ContextVar`` token
    reset (tokens are bound to the context that created them). Async dependencies instead
    run on the event loop task, keeping the whole generator in one consistent context.
    """
    if current_user.organization_id is None:
        raise UnauthorizedError("Platform admin accounts cannot access tenant-scoped routes")
    ctx = TenantContext(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        role=UserRole(current_user.role),
    )
    with tenant_context(ctx):
        yield ctx


TenantContextDep = Annotated[TenantContext, Depends(get_tenant_context)]


async def require_platform_admin(current_user: CurrentUser) -> None:
    """Router-level guard: use in ``APIRouter(dependencies=[Depends(require_platform_admin)])``.

    Checks the role directly, independent of ``TenantContext`` — platform admins have no
    organization to scope to.
    """
    if current_user.role != UserRole.PLATFORM_ADMIN:
        raise UnauthorizedError("Platform admin access required")
