# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Occurrence dates of a series.

A series begins at the first date on or after the start date that the rule
selects.  ``count`` counts every date of the series, skipped ones
included; ``until`` is inclusive.  Skipped dates are left out of listings.
"""
import civil
from errors import CommandError

STEP_CAP = 50000
MONTH_CAP = 12000


def daily(start, rule):
    d = start
    while d <= civil.MAX_DAY:
        yield d
        d += rule.every


def weekly(start, rule):
    ws = start
    wanted = rule.weekdays() or [civil.weekday(start)]
    d = start
    while d <= civil.MAX_DAY:
        week = (d - ws) // 7
        if week % rule.every:
            d = ws + 7 * (week + rule.every - week % rule.every)
            continue
        if civil.weekday(d) in wanted:
            yield d
        d += 1


def month_days(y, m, rule, start_day):
    dim = civil.days_in_month(y, m)
    if not rule.days:
        return [civil.days_from_civil(y, m, min(rule.monthday or start_day, dim))]
    first = civil.weekday(civil.days_from_civil(y, m, 1))
    found = set()
    for n, wd in rule.days:
        hits = list(range(1 + (wd - first) % 7, dim + 1, 7))
        if n > 0 and n <= len(hits):
            found.add(hits[n - 1])
        elif n < 0 and -n <= len(hits):
            found.add(hits[n])
    return [civil.days_from_civil(y, m, d) for d in sorted(found)]


def monthly(start, rule):
    sy, sm, sd = civil.civil_from_days(start)
    base = sy * 12 + sm - 1
    for k in range(MONTH_CAP):
        y, m0 = divmod(base + k * rule.every, 12)
        if y > 9999:
            return
        for d in month_days(y, m0 + 1, rule, sd):
            if d >= start:
                yield d


def yearly(start, rule):
    sy, sm, sd = civil.civil_from_days(start)
    for k in range(MONTH_CAP):
        y = sy + k * rule.every
        if y > 9999:
            return
        yield civil.days_from_civil(y, sm, min(sd, civil.days_in_month(y, sm)))


GENERATORS = {"daily": daily, "weekly": weekly, "monthly": monthly, "yearly": yearly}


def series(start, rule):
    """Every date of the series, in order, skips not applied."""
    if rule is None:
        yield start
        return
    produced = 0
    for d in GENERATORS[rule.freq](start, rule):
        if rule.until is not None and d > rule.until:
            return
        yield d
        produced += 1
        if rule.count is not None and produced >= rule.count:
            return


def between(ev, lo, hi, with_skips=False):
    """Dates of EV's series within LO..HI (inclusive)."""
    skipped = set() if with_skips else set(ev.skips)
    out = []
    steps = 0
    for d in series(ev.start // 86400, ev.rule):
        if d > hi:
            break
        steps += 1
        if steps > STEP_CAP:
            raise CommandError("too_far")
        if d >= lo and d not in skipped:
            out.append(d)
    return out


def first(ev, count, with_skips=False):
    """The first COUNT dates of the series (skipped ones left out unless WITH_SKIPS)."""
    skipped = set() if with_skips else set(ev.skips)
    out = []
    steps = 0
    for d in series(ev.start // 86400, ev.rule):
        steps += 1
        if steps > STEP_CAP:
            raise CommandError("too_far")
        if d not in skipped:
            out.append(d)
            if len(out) >= count:
                break
    return out
