# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Currency USD: US dollar, 2 decimals."""
import money

CODE = "USD"
NAME = "US dollar"
EXP = 2
RATE_PPM = 1000000
LATE_MIN = 200


def from_base(cents):
    return (cents * RATE_PPM + 500000) // 1000000


def to_base(minor):
    return money.div_half_up(minor * 1000000, RATE_PPM)


def text(amount):
    return money.fmt(amount, EXP)


def display(amount):
    return "%s %s" % (CODE, text(amount))


def minor_per_major():
    return 10 ** EXP


def rate_text():
    return money.fmt(RATE_PPM, 6)


def late_floor_text():
    return text(LATE_MIN)


def round_trip_gap(cents):
    """Base cents lost by converting CENTS out and back."""
    return cents - to_base(from_base(cents))


def whole_units(amount):
    return amount // minor_per_major()


def fraction(amount):
    return amount % minor_per_major()


def describe():
    return "%s exp=%d late_min=%s" % (CODE, EXP, late_floor_text())
