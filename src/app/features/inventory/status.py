from enum import StrEnum


class StockStatus(StrEnum):
    IN_STOCK = "inStock"
    LOW = "low"
    OUT = "out"


def derive_stock_status(qty: int, threshold: int) -> StockStatus:
    """Single source of truth for stock status (FR-STK-3); never persisted."""
    if qty <= 0:
        return StockStatus.OUT
    if qty <= threshold:
        return StockStatus.LOW
    return StockStatus.IN_STOCK


def quantity_ratio(qty: int, threshold: int) -> float:
    """Fill level for the quantity bar: the low threshold sits at the half-full mark."""
    if qty <= 0:
        return 0.0
    full = max(threshold * 2, 1)
    return round(min(qty / full, 1.0), 2)
