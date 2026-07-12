"""Single import point that ensures every feature model is registered on ``Base.metadata``.

Alembic's ``--autogenerate`` only sees models that have been imported. Feature model modules
are added here as they are implemented; ``migrations/env.py`` imports this module so the full
schema is present before diffing.
"""

from app.db.base import Base
from app.features.auth.models import User
from app.features.inventory.models import InventoryItem
from app.features.lenses.models import LensCoating, LensMaterial, LensTint, LensType
from app.features.patients.models import (
    LensConfig,
    Patient,
    PatientNote,
    VisitHistory,
)
from app.features.tips.models import Tip

__all__ = [
    "Base",
    "InventoryItem",
    "LensCoating",
    "LensConfig",
    "LensMaterial",
    "LensTint",
    "LensType",
    "Patient",
    "PatientNote",
    "Tip",
    "User",
    "VisitHistory",
]
