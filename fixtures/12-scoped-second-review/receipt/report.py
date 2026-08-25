"""Render a receipt."""

from receipt.parse import parse_amount
from receipt.total import total


def _dollars(cents):
    return "$%d.%02d" % divmod(cents, 100)


def render(lines):
    amounts = [parse_amount(line) for line in lines if line.strip()]
    out = [_dollars(amount) for amount in amounts]
    out.append("TOTAL " + _dollars(total(amounts)))
    return "\n".join(out)
