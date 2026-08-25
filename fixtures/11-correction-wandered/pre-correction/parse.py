"""Parse a decimal amount string into an amount."""


class AmountError(ValueError):
    """Raised when an amount cannot be parsed."""


def parse_amount(text):
    """Return the amount in dollars."""
    text = text.strip()
    if not text:
        raise AmountError("empty amount")
    try:
        return float(text)
    except ValueError:
        raise AmountError("malformed amount: %r" % text)
