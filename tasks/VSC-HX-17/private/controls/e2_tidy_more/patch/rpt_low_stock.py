# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Report low_stock: Slots at or below their reorder point."""
import reportutil
import stock

NAME = "low_stock"
TITLE = "Slots at or below their reorder point"


def run(w, cmd):
    cmd.allow("wh")
    want_wh, _ = reportutil.filters(w, cmd)
    count = 0
    for wh, sku in sorted(w.by_slot):
        if want_wh and wh != want_wh:
            continue
        cat = stock.category_of(sku)
        have = stock.available(w, wh, sku)
        if cat.needs_reorder(have):
            w.out.emit("  %s %s available=%d reorder=%d" % (wh, sku, have, cat.REORDER))
            count += 1
    if not count:
        w.out.emit("  (none)")
