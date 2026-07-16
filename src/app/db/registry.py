"""Single import point that ensures every feature model is registered on ``Base.metadata``.

Alembic's ``--autogenerate`` only sees models that have been imported. Feature model modules
are added here as they are implemented; ``migrations/env.py`` imports this module so the full
schema is present before diffing.
"""

from app.db.audit import register_audit_listeners
from app.db.base import Base
from app.features.auth.models import User
from app.features.import_forms.models import ImportForm
from app.features.intake.models import IntakeSubmission
from app.features.inventory.models import InventoryItem
from app.features.lenses.models import (
    LensCoating,
    LensMaterial,
    LensTint,
    LensType,
    Order,
    OrderItem,
)
from app.features.organizations.models import Organization
from app.features.patients.models import (
    LensConfig,
    Patient,
    PatientNote,
    VisitHistory,
)
from app.features.tips.models import Tip

register_audit_listeners()

__all__ = [
    "Base",
    "ImportForm",
    "IntakeSubmission",
    "InventoryItem",
    "LensCoating",
    "LensConfig",
    "LensMaterial",
    "LensTint",
    "LensType",
    "Order",
    "OrderItem",
    "Organization",
    "Patient",
    "PatientNote",
    "Tip",
    "User",
    "VisitHistory",
]
