"""Total a sequence of amounts."""


def total(amounts):
    """Return the exact total.

    Touched by cycle 1's correction: the previous body was
    `round(sum(amounts), 2)`, which is meaningless now that amounts
    arrive as whole cents.
    """
    return sum(amounts)
