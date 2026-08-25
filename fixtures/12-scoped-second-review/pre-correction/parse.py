"""Parse a decimal amount string into whole cents."""


class AmountError(ValueError):
    """Raised when an amount cannot be parsed."""


def parse_amount(text):
    """Return the amount in whole cents."""
    text = text.strip()
    if not text:
        raise AmountError("empty amount")
    whole, dot, frac = text.partition(".")
    if not whole.isdigit():
        raise AmountError("malformed amount: %r" % text)
    frac = frac.replace(".", "")[:2]
    return int(whole) * 100 + int(frac.ljust(2, "0") or "0")
