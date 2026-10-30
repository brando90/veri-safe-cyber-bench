# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Planned arrivals and lateness."""
import units


def delay_minutes(plan, actual):
    return (actual - plan) // units.MIN_MS


def late_stops(ship, slack):
    """Returns [(stop, arrival, delay minutes)] for stops later than the slack."""
    out = []
    for stop in sorted(ship.plan):
        actual = ship.arrival_at(stop)
        if actual is None:
            continue
        delay = delay_minutes(ship.plan[stop], actual)
        if delay > slack:
            out.append((stop, actual, delay))
    return out


def table(ship):
    lines = []
    for stop in sorted(ship.plan):
        actual = ship.arrival_at(stop)
        if actual is None:
            lines.append("plan stop %d eta=%s pending" % (stop, units.fmt_ms(ship.plan[stop])))
        else:
            lines.append("plan stop %d eta=%s delay=%dm" % (
                stop, units.fmt_ms(ship.plan[stop]), delay_minutes(ship.plan[stop], actual)))
    return lines
