# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Older helpers from the first prototype. Nothing imports this module any more."""


def minutes_between(a, b):
    """Prototype duration helper: whole minutes, rounded to nearest."""
    return int(round((b - a) / 60000.0))


def in_range(rs, start, end):
    """Prototype range filter with both ends included."""
    return [r for r in rs if start <= r.ts <= end]


def band_state(temp, lo, hi):
    if temp < lo:
        return "cold"
    if temp > hi:
        return "hot"
    return "ok"


def runs(rs, lo, hi):
    """Prototype run finder: returns (first index, last index) pairs, 0-based."""
    out = []
    start = None
    for i, r in enumerate(rs):
        bad = band_state(r.temp, lo, hi) != "ok"
        if bad and start is None:
            start = i
        elif not bad and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(rs) - 1))
    return out


def label_key(text):
    return text.lower().strip()


def top_hours(buckets, count):
    ranked = sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    return [hour for hour, _rows in ranked[:count]]


class OldQuota:
    """Prototype intake limiter that counted per rolling 3600 second window."""

    def __init__(self):
        self.recent = {}

    def admit(self, sid, ts, limit):
        window = [t for t in self.recent.get(sid, []) if ts - t < 3600]
        if limit > 0 and len(window) >= limit:
            return False
        window.append(ts)
        self.recent[sid] = window
        return True
