from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class InventorySeed:
    category: str
    name: str
    brand: str
    spec: str
    sku: str
    quantity: int
    threshold: int
    price: Decimal
    shape: str | None = None
    color: str | None = None


@dataclass(frozen=True)
class NoteSeed:
    en: str
    ar: str


@dataclass(frozen=True)
class VisitSeed:
    date: date
    title_en: str
    title_ar: str
    detail_en: str
    detail_ar: str


@dataclass(frozen=True)
class LensConfigSeed:
    lens_type: str
    material: str
    coatings: tuple[str, ...]
    tint: str
    frame_sku: str


@dataclass(frozen=True)
class PatientSeed:
    name_en: str
    name_ar: str
    phone: str
    town_en: str
    town_ar: str
    birth_year: int
    last_visit: date
    status: str
    rx_number: str
    rx_date: date
    od_sph: Decimal
    od_cyl: Decimal
    od_axis: int
    os_sph: Decimal
    os_cyl: Decimal
    os_axis: int
    pd_dist: Decimal
    pd_near: Decimal
    diagnosis_en: str
    diagnosis_ar: str
    tags: tuple[str, ...]
    od_add: Decimal | None = None
    os_add: Decimal | None = None
    notes: tuple[NoteSeed, ...] = field(default_factory=tuple)
    visits: tuple[VisitSeed, ...] = field(default_factory=tuple)
    lens_config: LensConfigSeed | None = None
