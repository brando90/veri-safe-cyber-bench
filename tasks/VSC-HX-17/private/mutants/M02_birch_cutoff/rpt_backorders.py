# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Report backorders: Units on backorder per sku."""
import orders
import reportutil

NAME = "backorders"
TITLE = "Units on backorder per sku"


def run(w, cmd):
    cmd.allow()
    rows = {}
    for order in orders.live(w):
        for line in order.lines:
            if line.backorder > 0:
                rows[line.sku] = rows.get(line.sku, 0) + line.backorder
    reportutil.emit_groups(w, rows, "units")
