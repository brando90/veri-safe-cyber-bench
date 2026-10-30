# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Counts over the store."""
import timeparse


def cmd_stats(w, cmd):
    rows = w.store.ordered()
    w.emit("events %d, recurring %d, all-day %d" % (
        len(rows), sum(1 for e in rows if e.rule), sum(1 for e in rows if e.allday)))
    counts = {}
    for ev in rows:
        for c in ev.cats:
            counts[c] = counts.get(c, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    for name, n in ranked[:5]:
        w.emit("category %s %d" % (name, n))
    if rows:
        first = min(rows, key=lambda e: e.start)
        last = max(rows, key=lambda e: e.start)
        w.emit("earliest %s %s" % (first.id, timeparse.format_date(first.start // 86400)))
        w.emit("latest %s %s" % (last.id, timeparse.format_date(last.start // 86400)))
        span = last.start // 86400 - first.start // 86400
        w.emit("span %d days (%d weeks)" % (span, span // 7))
    skipped = sum(len(e.skips) for e in rows)
    w.emit("skips %d" % skipped)
