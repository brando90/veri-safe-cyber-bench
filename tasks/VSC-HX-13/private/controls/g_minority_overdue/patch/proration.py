# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Part-period fees."""
import money
import timeutil


def days_left(day):
    """Days from DAY to the last day of its period, both included."""
    return timeutil.end(timeutil.period_of(day)) - day + 1


def share(fee, days):
    """The part of a whole-period FEE that covers DAYS days."""
    return money.div_half_up(fee * days, timeutil.PERIOD)
