# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Sliding-window activity counts per source and the alerts built from them."""
import stamp


def peak(times, window):
    """The most records of one source inside any span of WINDOW seconds.

    TIMES are record times in whole seconds.  A record counts for the window
    ending at time t when t - WINDOW < its time <= t.
    """
    times = sorted(times)
    best = 0
    lo = 0
    for hi, t in enumerate(times):
        while t - times[lo] >= window:
            lo += 1
        best = max(best, hi - lo + 1)
    return best


def by_source(records):
    groups = {}
    for record in records:
        groups.setdefault(record.source, []).append(stamp.seconds(record.when))
    return groups


def alerts(records, window, limit_for):
    """Sources whose peak count is more than their limit: (source, peak, limit)."""
    found = []
    groups = by_source(records)
    for source in sorted(groups):
        top = peak(groups[source], window)
        limit = limit_for(source)
        if top > limit:
            found.append((source, top, limit))
    return found


def at_limit(records, window, limit_for):
    """Sources whose peak count equals their limit exactly."""
    out = []
    groups = by_source(records)
    for source in sorted(groups):
        if peak(groups[source], window) == limit_for(source):
            out.append(source)
    return out
