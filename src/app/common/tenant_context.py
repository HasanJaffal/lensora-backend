import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from app.common.exceptions import TenantContextMissingError
from app.features.auth.models import UserRole


@dataclass(frozen=True, slots=True)
class TenantContext:
    """The authenticated tenant boundary for the current request or CLI invocation."""

    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: UserRole


_current_tenant_context: ContextVar[TenantContext | None] = ContextVar(
    "current_tenant_context", default=None
)


@contextmanager
def tenant_context(ctx: TenantContext) -> Iterator[None]:
    """Bind ``ctx`` to the current context for non-request paths (CLI, management commands, seed).

    FastAPI requests set the ContextVar via the ``get_tenant_context`` dependency instead.
    """
    token = _current_tenant_context.set(ctx)
    try:
        yield
    finally:
        _current_tenant_context.reset(token)


def get_tenant_context() -> TenantContext | None:
    return _current_tenant_context.get()


def require_tenant_context() -> TenantContext:
    ctx = _current_tenant_context.get()
    if ctx is None:
        raise TenantContextMissingError("No tenant context is bound to the current execution")
    return ctx
