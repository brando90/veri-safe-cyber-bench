# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""``latency [RECIPIENT]`` and ``timeline ID``: delivery-time diagnostics.

Latency is measured per finished message, from acceptance to the instant
the last fragment was acknowledged (``finished_at``).  Percentiles use the
nearest-rank method on the sorted sample: the P-th percentile of N values
is the value at 1-based rank ceil(P * N / 100), so the 100th percentile is
the maximum and every percentile is an observed value.  Integer arithmetic
only; no interpolation.
"""

import model
import timefmt

PERCENTILES = (50, 90, 99, 100)

# Histogram buckets, upper bounds in milliseconds (inclusive), then "more".
BUCKETS = (
    ("<=1s", 1000),
    ("<=10s", 10 * 1000),
    ("<=1min", 60 * 1000),
    ("<=10min", 10 * 60 * 1000),
    ("<=1h", 60 * 60 * 1000),
)


def nearest_rank(sorted_values, pct):
    """The PCT-th percentile of SORTED_VALUES (non-empty, ascending)."""
    n = len(sorted_values)
    rank = -(-pct * n // 100)       # ceil without floats
    if rank < 1:
        rank = 1
    return sorted_values[rank - 1]


def samples(svc, recipient=None):
    """Latencies (ms) of delivered messages, optionally for one recipient."""
    out = []
    for msg in svc.messages.values():
        if msg.state != model.DELIVERED or msg.finished_at is None:
            continue
        if recipient is not None and msg.recipient != recipient:
            continue
        out.append(msg.finished_at - msg.accepted_at)
    out.sort()
    return out


def histogram(values):
    counts = [0] * (len(BUCKETS) + 1)
    for v in values:
        for i, (_, bound) in enumerate(BUCKETS):
            if v <= bound:
                counts[i] += 1
                break
        else:
            counts[-1] += 1
    labels = [label for label, _ in BUCKETS] + [">1h"]
    return list(zip(labels, counts))


def latency_lines(svc, recipient=None):
    values = samples(svc, recipient)
    scope = "all" if recipient is None else recipient
    out = ["latency %s delivered=%d" % (scope, len(values))]
    if not values:
        return out
    parts = ["p%d=%s" % (p, timefmt.fmt_seconds(nearest_rank(values, p))) for p in PERCENTILES]
    out.append(" ".join(parts))
    out.append("min=%s mean=%s" % (timefmt.fmt_seconds(values[0]),
                                   timefmt.fmt_seconds(sum(values) // len(values))))
    for label, count in histogram(values):
        if count:
            out.append("  %-8s %d" % (label, count))
    return out


def _attempts_text(msg):
    return ",".join(str(f.attempts) for f in msg.frags)


def timeline_lines(msg):
    """Every recorded event of MSG with the time since acceptance."""
    out = ["timeline %s %s->%s state=%s attempts=%s" % (
        msg.id, msg.sender, msg.recipient, msg.state, _attempts_text(msg))]
    for at, text in msg.history:
        delta = at - msg.accepted_at
        out.append("  +%s %s" % (timefmt.fmt_seconds(delta), text))
    if msg.finished_at is not None:
        out.append("  total %s" % timefmt.fmt_seconds(msg.finished_at - msg.accepted_at))
    return out
