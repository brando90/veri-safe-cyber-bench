# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Calendar helpers: day 0 is a Monday, days count up from there."""

NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
WEEK = 7


def weekday(day):
    return day % WEEK


def name_of(day):
    return NAMES[weekday(day)]


def next_open(day, open_days):
    """The first day on or after DAY whose weekday is in OPEN_DAYS."""
    while weekday(day) not in open_days:
        day += 1
    return day


def next_free(day, closed_days):
    """The first day on or after DAY whose weekday is not in CLOSED_DAYS."""
    while weekday(day) in closed_days:
        day += 1
    return day


def days_text(days):
    return ",".join(NAMES[d] for d in sorted(days)) or "-"


def span(first, last):
    """Whole days from FIRST to LAST, both ends included."""
    return last - first + 1
