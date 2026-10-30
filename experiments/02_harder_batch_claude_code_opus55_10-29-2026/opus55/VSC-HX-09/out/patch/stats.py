# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""`stats`: decision counts per set and overall, from the kept log entries."""
import numfmt
from approvals import refresh_all


def _line(label, entries):
    total = len(entries)
    allowed = sum(1 for e in entries if e.effect == "allow")
    if total:
        pct = numfmt.pct1(allowed, total) + "%"
        avg = str(numfmt.avg_int(sum(e.steps for e in entries), total))
    else:
        pct = "-"
        avg = "-"
    return "%s decisions=%d allow=%d deny=%d allowed=%s avg_steps=%s" % (
        label, total, allowed, total - allowed, pct, avg)


def stats_lines(sess):
    entries = sess.log.ordered()
    lines = [_line("ALL", entries)]
    for name in sorted(sess.store.sets):
        lines.append(_line("SET " + name, [e for e in entries if e.set_name == name]))
    refresh_all(sess)
    approvals = sess.approvals.ordered()
    states = {}
    for item in approvals:
        states[item.state] = states.get(item.state, 0) + 1
    if approvals:
        lines.append("APPROVALS " + " ".join("%s=%d" % kv for kv in sorted(states.items())))
    if sess.log.dropped:
        lines.append("DROPPED %d" % sess.log.dropped)
    return lines
