# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Money: exact amounts in cents (fractions.Fraction), rounded once per line.

Every billed line is rounded to whole cents, half up.  Every total,
subtotal and report figure is the sum of the rounded line amounts.
"""

from fractions import Fraction


def cents(amount):
    """Round a non-negative Fraction of cents to whole cents, half up."""
    num, den = amount.numerator, amount.denominator
    return (2 * num + den) // (2 * den)


def total(amounts):
    """Total in whole cents of a sequence of exact line amounts."""
    return sum(cents(a) for a in amounts)


def fmt(whole_cents):
    sign = "-" if whole_cents < 0 else ""
    c = abs(whole_cents)
    return "%s%d.%02d" % (sign, c // 100, c % 100)


def parse_rate(text):
    """'1.5' -> Fraction(3, 2) (cents)."""
    return Fraction(text)
