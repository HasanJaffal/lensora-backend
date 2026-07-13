from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

DEFAULT_DEPOSIT_PERCENT = Decimal("0.40")
_CENTS = Decimal("0.01")


@dataclass(frozen=True)
class LineItem:
    label_en: str
    label_ar: str
    price: Decimal


@dataclass(frozen=True)
class PricedOrder:
    items: tuple[LineItem, ...]
    total: Decimal
    deposit: Decimal
    deposit_percent: Decimal


def price_order(
    items: tuple[LineItem, ...],
    *,
    deposit_percent: Decimal = DEFAULT_DEPOSIT_PERCENT,
) -> PricedOrder:
    """Pure order pricing: sum the line items and apply the deposit percentage.

    Given selections it always yields the same itemized total, so it is unit-testable
    in isolation from the database and the web layer.
    """
    total = sum((item.price for item in items), Decimal("0")).quantize(_CENTS)
    deposit = (total * deposit_percent).quantize(_CENTS, rounding=ROUND_HALF_UP)
    return PricedOrder(
        items=items,
        total=total,
        deposit=deposit,
        deposit_percent=deposit_percent,
    )
