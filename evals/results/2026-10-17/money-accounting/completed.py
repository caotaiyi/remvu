from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def parse_cents(amount: str) -> int:
    text = amount.strip()
    if text.startswith("(") and text.endswith(")"):
        # Accounting style: (12.345) means a negative amount; a sign inside is invalid.
        inner = text[1:-1].strip()
        if inner.startswith(("+", "-")):
            raise InvalidOperation(f"signed amount inside parentheses: {amount!r}")
        value = -Decimal(inner)
    else:
        value = Decimal(text)
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
