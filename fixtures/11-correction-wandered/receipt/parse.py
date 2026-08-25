"""Parse a decimal amount string into whole cents."""


class AmountError(ValueError):
    """Raised when an amount cannot be parsed."""


def parse_amount(text):
    """Return the amount in whole cents.

    Rewritten by cycle 1's correction. The previous body was
    `round(float(text) * 100)`, which the review found could not be exact
    for the values the criterion names.
    """
    text = text.strip()
    if not text:
        raise AmountError("empty amount")
    whole, dot, frac = text.partition(".")
    if not whole.isdigit():
        raise AmountError("malformed amount: %r" % text)
    if dot and (not frac.isdigit() or len(frac) > 2):
        raise AmountError("malformed amount: %r" % text)
    return int(whole) * 100 + int((frac or "0").ljust(2, "0"))
