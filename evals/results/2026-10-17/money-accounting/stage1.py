from decimal import Decimal, ROUND_HALF_UP


def parse_cents(amount: str) -> int:
    value = Decimal(amount.strip())
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
