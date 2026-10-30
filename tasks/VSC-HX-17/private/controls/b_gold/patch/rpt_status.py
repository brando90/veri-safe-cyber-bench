# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Report status: Orders per status."""
import orders
import reportutil

NAME = "status"
TITLE = "Orders per status"
ORDER = ("open", "partial", "backorder", "shipped", "cancelled")


def run(w, cmd):
    cmd.allow()
    rows = {}
    for order in orders.all_sorted(w):
        rows[order.status] = rows.get(order.status, 0) + 1
    reportutil.emit_groups(w, rows, "units", order=ORDER)
