from dataclasses import dataclass, field


@dataclass(frozen=True)
class PatientSummary:
    """Minimal patient fields shared with the AI provider (NFR-5 scoped context)."""

    name: str
    town: str
    age: int
    status: str
    diagnosis: str | None
    od_sph: str | None
    os_sph: str | None


@dataclass(frozen=True)
class StockSummary:
    name: str
    sku: str
    quantity: int
    status: str


@dataclass(frozen=True)
class AssistantContext:
    patients: list[PatientSummary] = field(default_factory=list)
    low_stock: list[StockSummary] = field(default_factory=list)


@dataclass(frozen=True)
class FrameSummary:
    name: str
    brand: str
    shape: str | None
    color: str | None


@dataclass(frozen=True)
class StylingContext:
    frame: FrameSummary
    need: str
    diagnosis: str | None
