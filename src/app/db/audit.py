"""Centralized audit stamping: the single source of truth for ``created_by``/``updated_by``.

Registers mapper-level ``before_insert``/``before_update`` listeners once against
``AuditMixin`` with ``propagate=True``, so every model that inherits it — via ``Entity`` or
``TenantEntity`` — is stamped automatically. No feature service ever sets these columns itself.
"""

from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Mapper

from app.common.tenant_context import get_tenant_context
from app.db.base import AuditMixin, Entity, TenantEntity, TenantMixin


def _stamp_created_by(mapper: Mapper[Any], connection: object, target: AuditMixin) -> None:
    ctx = get_tenant_context()
    if ctx is None:
        return
    target.created_by = ctx.user_id
    target.updated_by = ctx.user_id
    if isinstance(target, TenantMixin):
        target.organization_id = ctx.organization_id


def _stamp_updated_by(mapper: Mapper[Any], connection: object, target: AuditMixin) -> None:
    ctx = get_tenant_context()
    if ctx is None:
        return
    target.updated_by = ctx.user_id


def register_audit_listeners() -> None:
    """Attach the listeners once to the two mapped audit bases, cascading to every subclass."""
    for base in (Entity, TenantEntity):
        event.listen(base, "before_insert", _stamp_created_by, propagate=True)
        event.listen(base, "before_update", _stamp_updated_by, propagate=True)
