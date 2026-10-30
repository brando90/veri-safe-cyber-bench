# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""expire: write off expired lots and put their reservations back on backorder."""
import orders
import stock
import warehouses


def requeue(w, lot):
    """Move every reservation on LOT back to its order line's backorder."""
    moved = 0
    for order in orders.all_sorted(w):
        for line in order.lines:
            for alloc in list(line.allocs):
                if alloc[1] == lot.id:
                    line.allocs.remove(alloc)
                    line.backorder += alloc[2]
                    lot.reserved -= alloc[2]
                    moved += alloc[2]
        orders.refresh(order)
    return moved


def cmd_expire(w, cmd):
    cmd.allow()
    code = cmd.arg(0, "")
    if code:
        warehouses.checked(code)
    count = 0
    for lot in sorted(w.lots.values(), key=lambda x: x.id):
        if code and lot.wh != code:
            continue
        if not stock.category_of(lot.sku).is_expired(lot.expiry, w.day):
            continue
        moved = requeue(w, lot)
        stock.record(w, "expire", lot.wh, lot.sku, -lot.qty, ref=lot.id)
        w.out.emit("expired lot %s %s %s qty %d requeued %d" % (lot.id, lot.wh, lot.sku, lot.qty, moved))
        stock.remove_lot(w, lot)
        count += 1
    w.audit_add("expire", code or "all", count)
    w.out.emit("%d lots expired" % count)
