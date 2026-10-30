# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Degree-minutes spent outside the band."""
import excursions
import units


def degree_minutes_tenths(rs, lo, hi):
    """Sum over consecutive pairs of deviation (tenths) times elapsed minutes, in tenths of a degree-minute."""
    total = 0
    for a, b in zip(rs, rs[1:]):
        dev = 0 if lo <= a.temp <= hi else excursions.deviation(a.temp, lo, hi)
        total += dev * (b.ts - a.ts)
    return units.div_round_half_up(total, units.MIN_MS)


def worst_hour(rs, lo, hi):
    """Returns (hour index, out-of-band reading count) of the hour with most such readings, or None."""
    counts = {}
    for r in rs:
        if not lo <= r.temp <= hi:
            hour = r.ts // units.HOUR_MS
            counts[hour] = counts.get(hour, 0) + 1
    if not counts:
        return None
    best = max(counts.values())
    return min(h for h, n in counts.items() if n == best), best
