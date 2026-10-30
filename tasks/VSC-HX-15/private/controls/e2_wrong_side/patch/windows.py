# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Time-range selection over a time-ordered reading list."""
from bisect import bisect_left, bisect_right

import units


def _ts(reading):
    return reading.ts


def select(rs, start, end):
    first = bisect_left(rs, start, key=_ts)
    last = bisect_right(rs, end, key=_ts)
    return rs[first:last]


def by_hour(rs):
    buckets = {}
    for r in rs:
        buckets.setdefault(r.ts // units.HOUR_MS, []).append(r)
    return buckets
