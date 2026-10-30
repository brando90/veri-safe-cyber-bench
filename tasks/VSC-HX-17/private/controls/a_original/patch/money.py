# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Integer helpers.  Money is a whole number of US cents; weights are grams."""
import re

from errors import CommandError

AMOUNT_MAX = 10 ** 9


def ceil_div(num, den):
    return -((-num) // den)


def div_half_up(num, den):
    """NUM / DEN rounded to the nearest integer, halves away from zero."""
    if num < 0:
        return -div_half_up(-num, den)
    return (2 * num + den) // (2 * den)


def pct(amount, bp):
    """BP basis points of AMOUNT, rounded half up."""
    return div_half_up(amount * bp, 10000)


def fmt(amount):
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    return "%s%d.%02d" % (sign, amount // 100, amount % 100)


def parse(text):
    """Cents for the decimal TEXT (at most two decimals), or an error."""
    if not re.fullmatch(r"[0-9]{1,9}(\.[0-9]{1,2})?", text):
        raise CommandError("bad_number", text)
    whole, _, frac = text.partition(".")
    value = int(whole) * 100 + int((frac + "00")[:2])
    if value <= 0 or value > AMOUNT_MAX:
        raise CommandError("bad_number", text)
    return value


def parse_int(text, low, high):
    if not re.fullmatch(r"[0-9]{1,9}", text):
        raise CommandError("bad_number", text)
    value = int(text)
    if value < low or value > high:
        raise CommandError("bad_number", text)
    return value


def parse_signed(text, limit):
    if not re.fullmatch(r"[+-]?[0-9]{1,9}", text):
        raise CommandError("bad_delta", text)
    value = int(text)
    if value == 0 or abs(value) > limit:
        raise CommandError("bad_delta", text)
    return value


def grams(weight):
    return "%dg" % weight


def ratio_text(part, whole):
    """PART / WHOLE as a percentage with one decimal, for listings."""
    if whole <= 0:
        return "0.0%"
    tenths = div_half_up(part * 1000, whole)
    return "%d.%d%%" % (tenths // 10, tenths % 10)


def clamp(value, low, high):
    return max(low, min(high, value))
