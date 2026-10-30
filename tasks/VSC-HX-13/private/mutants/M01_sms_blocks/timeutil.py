# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Day numbers, billing periods and due dates.

Time is a whole number of days since the start of the run.  Billing periods
are fixed blocks of PERIOD days: period n covers days n*PERIOD up to
n*PERIOD+PERIOD-1.
"""

PERIOD = 30
MAX_TICK = 400


def period_of(day):
    return day // PERIOD


def start(period):
    return period * PERIOD


def end(period):
    return period * PERIOD + PERIOD - 1


def due_day(issued, terms):
    return issued + terms


def is_overdue(today, due):
    """An invoice is overdue from the day after its due day."""
    return today > due


def overdue_days(today, due):
    return max(0, today - due)


def label(period):
    return "p%02d" % period


def span_text(period):
    return "days %d-%d" % (start(period), end(period))


def days_between(first, last):
    return max(0, last - first)


def periods_between(first_day, last_day):
    """Number of period boundaries crossed going from FIRST_DAY to LAST_DAY."""
    return max(0, period_of(last_day) - period_of(first_day))


def first_day_of_next(day):
    return start(period_of(day) + 1)


def is_period_start(day):
    return day % PERIOD == 0
