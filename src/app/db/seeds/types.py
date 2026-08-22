from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class LensOptionSeed:
    name_en: str
    name_ar: str
    description_en: str
    description_ar: str
    price: Decimal


@dataclass(frozen=True)
class TipSeed:
    category: str
    tags: tuple[str, ...]
    icon: str
    color: str
    title_en: str
    title_ar: str
    body_en: str
    body_ar: str
