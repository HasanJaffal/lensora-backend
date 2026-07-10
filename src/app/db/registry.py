"""Single import point that ensures every feature model is registered on ``Base.metadata``.

Alembic's ``--autogenerate`` only sees models that have been imported. Feature model modules
are added here as they are implemented (Task 06 onward); ``migrations/env.py`` imports this
module so the full schema is present before diffing.
"""

from app.db.base import Base

__all__ = ["Base"]
