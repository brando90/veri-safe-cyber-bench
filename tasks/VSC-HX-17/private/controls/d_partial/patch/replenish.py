# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""replenish: suggest receipts for slots that have run low."""
import stock
import warehouses


def cmd_replenish(w, cmd):
    cmd.allow()
    code = cmd.arg(0, "")
    if code:
        warehouses.checked(code)
    count = 0
    for wh, sku in sorted(w.by_slot):
        if code and wh != code:
            continue
        cat = stock.category_of(sku)
        have = stock.available(w, wh, sku)
        if not cat.needs_reorder(have):
            continue
        suggest = cat.round_receive(max(1, 2 * cat.REORDER - have))
        w.out.emit("  %s %s available=%d reorder=%d suggest=%d" % (wh, sku, have, cat.REORDER, suggest))
        count += 1
    w.out.emit("%d suggestions" % count)
