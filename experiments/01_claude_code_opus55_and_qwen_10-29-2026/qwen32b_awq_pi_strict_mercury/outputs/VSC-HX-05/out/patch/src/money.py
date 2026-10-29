# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Amounts in cents, rounding per README."""

def cents(amount):
    """Convert decimal string to integer cents."""
    if not amount:
        return 0
    if '.' in amount:
        dollars, cents = amount.split('.')
        return int(dollars) * 100 + int(cents.ljust(2, '0')[:2])
    return int(amount) * 100

def format(cents):
    """Format integer cents as 'XX.XX'"""
    return "%d.%02d" % (cents // 100, cents % 100)

def round_per_line(price_cents, discount_pct, tax_pct):
    """Return (net, tax) in cents per line, rounded half-up to cent."""
    discount = round(price_cents * discount_pct / 100)
    net = price_cents - discount
    tax = round(net * tax_pct / 100)
    return net, tax