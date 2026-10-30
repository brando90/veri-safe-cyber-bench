# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Report credits: Credit held per customer."""
import currencies
import customers
import reportutil

NAME = "credits"
TITLE = "Credit held per customer"


def run(w, cmd):
    cmd.allow("cur")
    want_cur, _ = reportutil.filters(w, cmd)
    rows = {}
    for cust in customers.all_sorted(w):
        if want_cur and cust.currency != want_cur:
            continue
        if cust.credit > 0:
            rows[(cust.id, cust.currency)] = cust.credit
    reportutil.emit_groups(w, rows)
