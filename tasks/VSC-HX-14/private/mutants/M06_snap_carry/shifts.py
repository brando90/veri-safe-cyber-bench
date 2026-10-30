# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Date arithmetic: add days, weeks, months or years to a date.

Months and years keep the day of the month when they can; a result day
that the target month lacks becomes that month's last day.
"""
import civil
from errors import CommandError

UNIT_NAMES = {"day": "d", "days": "d", "d": "d", "week": "w", "weeks": "w", "w": "w",
              "month": "m", "months": "m", "m": "m", "year": "y", "years": "y", "y": "y"}


def add_months(day, n):
    y, m, d = civil.civil_from_days(day)
    y2, m0 = divmod(y * 12 + (m - 1) + n, 12)
    if not 1 <= y2 <= 9999:
        raise CommandError("out_of_range")
    return civil.days_from_civil(y2, m0 + 1, min(d, civil.days_in_month(y2, m0 + 1)))


def shift(day, n, unit):
    kind = UNIT_NAMES.get(unit)
    if kind is None:
        raise CommandError("bad_unit", unit)
    if kind == "d":
        out = day + n
    elif kind == "w":
        out = day + 7 * n
    elif kind == "m":
        out = add_months(day, n)
    else:
        out = add_months(day, 12 * n)
    if not civil.in_range(out):
        raise CommandError("out_of_range")
    return out
