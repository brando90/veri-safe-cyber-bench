# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Report aging: Outstanding amount by days overdue."""
import invoice
import reportutil
import timeutil

NAME = "aging"
TITLE = "Outstanding amount by days overdue"
BUCKETS = (("current", 0), ("1-30", 30), ("31-60", 60), ("61-90", 90), ("91+", None))


def bucket_of(days):
    if days == 0:
        return "current"
    for label, top in BUCKETS[1:]:
        if top is None or days <= top:
            return label
    return BUCKETS[-1][0]


def run(w, cmd):
    cmd.allow("cur", "cust")
    want_cur, want_cust = reportutil.filters(w, cmd)
    rows = {}
    for inv in invoice.live(w):
        if want_cur and inv.currency != want_cur:
            continue
        if want_cust and inv.cust != want_cust:
            continue
        owed = inv.outstanding()
        if owed <= 0:
            continue
        label = bucket_of(timeutil.overdue_days(w.day, inv.due))
        k = (label, inv.currency)
        rows[k] = rows.get(k, 0) + owed
    order = [label for label, _ in BUCKETS]
    reportutil.emit_groups(w, rows, order=order)
