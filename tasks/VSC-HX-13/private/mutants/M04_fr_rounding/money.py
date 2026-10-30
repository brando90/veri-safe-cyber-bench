# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Integer money helpers.  Amounts are whole minor units of one currency."""
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


def fmt(amount, exp):
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    if exp == 0:
        return "%s%d" % (sign, amount)
    scale = 10 ** exp
    return "%s%d.%0*d" % (sign, amount // scale, exp, amount % scale)


def parse(text, exp):
    """Minor units for the decimal TEXT (at most EXP decimals), or an error."""
    pattern = r"[0-9]{1,9}" if exp == 0 else r"[0-9]{1,9}(\.[0-9]{1,%d})?" % exp
    if not re.fullmatch(pattern, text):
        raise CommandError("bad_amount", text)
    whole, _, frac = text.partition(".")
    value = int(whole) * 10 ** exp + int((frac + "0" * exp)[:exp] or 0)
    if value <= 0 or value > AMOUNT_MAX:
        raise CommandError("bad_amount", text)
    return value


def parse_int(text, low, high):
    if not re.fullmatch(r"[0-9]{1,9}", text):
        raise CommandError("bad_number", text)
    value = int(text)
    if value < low or value > high:
        raise CommandError("bad_number", text)
    return value


def clamp(value, low, high):
    return max(low, min(high, value))


def split_even(amount, parts):
    """AMOUNT cut into PARTS pieces that differ by at most one unit and add
    up to AMOUNT; the larger pieces come first."""
    base, extra = divmod(amount, parts)
    return [base + 1 if i < extra else base for i in range(parts)]


def ratio_text(part, whole):
    """PART / WHOLE as a percentage with one decimal, for listings."""
    if whole <= 0:
        return "0.0%"
    tenths = div_half_up(part * 1000, whole)
    return "%d.%d%%" % (tenths // 10, tenths % 10)


def sum_text(amounts, exp):
    return fmt(sum(amounts), exp)
