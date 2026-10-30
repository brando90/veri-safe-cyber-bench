# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Hourly statistics."""
import units
import windows


def hourly(rs):
    rows = []
    buckets = windows.by_hour(rs)
    for hour in sorted(buckets):
        part = buckets[hour]
        temps = [r.temp for r in part]
        hums = [r.hum for r in part if r.hum is not None]
        avg = units.div_round_half_up(sum(temps), len(temps))
        hum = "-" if not hums else str(units.div_round_half_up(sum(hums), len(hums)))
        rows.append("hour %d n=%d min=%s max=%s avg=%s hum=%s" % (
            hour, len(part), units.fmt_tenths(min(temps)), units.fmt_tenths(max(temps)),
            units.fmt_tenths(avg), hum))
    return rows


def median(sorted_temps):
    n = len(sorted_temps)
    mid = n // 2
    if n % 2:
        return sorted_temps[mid]
    return units.div_round_half_up(sorted_temps[mid - 1] + sorted_temps[mid], 2)


def nearest_rank(sorted_temps, percent):
    rank = (percent * len(sorted_temps) + 99) // 100
    return sorted_temps[max(rank, 1) - 1]


def describe(rs):
    """Returns a text line, or None when there is nothing to describe."""
    if not rs:
        return None
    temps = sorted(r.temp for r in rs)
    mean = units.div_round_half_up(sum(temps), len(temps))
    return "n=%d min=%s p50=%s p90=%s max=%s mean=%s" % (
        len(temps), units.fmt_tenths(temps[0]), units.fmt_tenths(median(temps)),
        units.fmt_tenths(nearest_rank(temps, 90)), units.fmt_tenths(temps[-1]),
        units.fmt_tenths(mean))


def histogram(rs, step):
    """Counts readings per bucket [start, start + step); starts are multiples of step."""
    counts = {}
    for r in rs:
        start = (r.temp // step) * step
        counts[start] = counts.get(start, 0) + 1
    return sorted(counts.items())
