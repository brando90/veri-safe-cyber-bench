# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Busy time: occurrences that start in a UTC window, merged into spans.

Spans that overlap or touch are merged into one.
"""
import agenda
import durations
import timeparse
from errors import CommandError


def merge(spans):
    out = []
    for start, end in sorted(spans):
        if out and start < out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return out


def cmd_busy(w, cmd):
    lo = timeparse.parse_date(cmd.arg(0))
    hi = timeparse.parse_date(cmd.arg(1))
    if hi < lo:
        raise CommandError("bad_order")
    if hi - lo + 1 > 400:
        raise CommandError("window_too_big", 400)
    spans = [(e.utc, e.utc + e.ev.dur) for e in agenda.entries(w.store, lo, hi)]
    merged = merge(spans)
    for start, end in merged:
        w.emit("%sZ %sZ %s" % (timeparse.format_instant(start), timeparse.format_instant(end),
                               durations.fmt(end - start)))
    w.emit("busy %s in %d spans" % (durations.fmt(sum(e - s for s, e in merged)), len(merged)))
