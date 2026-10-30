# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Report payments: Payments received per day."""
import reportutil

NAME = "payments"
TITLE = "Payments received per day"


def run(w, cmd):
    cmd.allow("cur", "cust")
    want_cur, want_cust = reportutil.filters(w, cmd)
    rows = {}
    for e in w.ledger:
        if e.kind != "payment":
            continue
        if want_cust and e.cust != want_cust:
            continue
        if want_cur and w.customers[e.cust].currency != want_cur:
            continue
        k = ("day%04d" % e.day, w.customers[e.cust].currency)
        rows[k] = rows.get(k, 0) + e.amount
    reportutil.emit_groups(w, rows)
