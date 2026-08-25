"""Render a receipt."""

from receipt.parse import parse_amount
from receipt.total import total


def render(lines):
    amounts = [parse_amount(line) for line in lines if line.strip()]
    out = ["$%.2f" % amount for amount in amounts]
    out.append("TOTAL $%.2f" % total(amounts))
    return "\n".join(out)
