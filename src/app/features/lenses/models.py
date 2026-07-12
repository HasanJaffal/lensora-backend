from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin


class LensOptionMixin:
    """Shared columns for every lens catalog (type, material, coating, tint).

    ``price`` is the price delta added to the order total; a value of 0 means the
    option is included at no extra cost (e.g. the standard 1.50 material).
    """

    name_en: Mapped[str] = mapped_column(String(255))
    name_ar: Mapped[str] = mapped_column(String(255))
    description_en: Mapped[str] = mapped_column(String(500))
    description_ar: Mapped[str] = mapped_column(String(500))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))


class LensType(Base, UuidPrimaryKeyMixin, TimestampMixin, LensOptionMixin):
    __tablename__ = "lens_types"


class LensMaterial(Base, UuidPrimaryKeyMixin, TimestampMixin, LensOptionMixin):
    __tablename__ = "lens_materials"


class LensCoating(Base, UuidPrimaryKeyMixin, TimestampMixin, LensOptionMixin):
    __tablename__ = "lens_coatings"


class LensTint(Base, UuidPrimaryKeyMixin, TimestampMixin, LensOptionMixin):
    __tablename__ = "lens_tints"
