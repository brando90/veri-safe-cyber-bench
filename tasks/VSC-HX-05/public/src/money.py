# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Money and percentage arithmetic.

All amounts are integer cents.  Rates are integer basis points (1/100 of a
percent): 8.25 % is 825.  Floats are never used for money.

Rounding rule (README, "Money"): a percentage of an amount is computed for
each invoice line separately and rounded half up to the cent; totals are the
sums of those rounded line amounts.
"""

import re

MONEY_RE = re.compile(r"(\d{1,6})(?:\.(\d{1,2}))?\Z")
RATE_RE = re.compile(r"(\d{1,3})(?:\.(\d{1,2}))?\Z")
MAX_RATE_BP = 10000


def parse_cents(text):
    """'12.5' -> 1250, '7' -> 700; None if TEXT is not a valid amount."""
    m = MONEY_RE.match(text)
    if not m:
        return None
    whole = int(m.group(1))
    frac = (m.group(2) or "").ljust(2, "0")
    return whole * 100 + int(frac or "0")


def parse_rate(text):
    """'8.25' -> 825 basis points; None if invalid or above 100 %."""
    m = RATE_RE.match(text)
    if not m:
        return None
    whole = int(m.group(1))
    frac = (m.group(2) or "").ljust(2, "0")
    bp = whole * 100 + int(frac or "0")
    if bp > MAX_RATE_BP:
        return None
    return bp


def fmt(cents):
    """1250 -> '12.50', -5 -> '-0.05'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "%s%d.%02d" % (sign, cents // 100, cents % 100)


def fmt_rate(bp):
    """825 -> '8.25'."""
    return "%d.%02d" % (bp // 100, bp % 100)


def pct_of(cents, bp):
    """BP basis points of CENTS, rounded half up (half away from zero)."""
    if cents < 0:
        return -pct_of(-cents, bp)
    return (cents * bp + 5000) // 10000


def line_amounts(price, discount_pct, tax_bp):
    """Amounts of one invoice line: (discount, net, tax, total)."""
    discount = pct_of(price, discount_pct * 100)
    net = price - discount
    tax = pct_of(net, tax_bp)
    return discount, net, tax, net + tax
