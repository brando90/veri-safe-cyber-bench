# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""adjust: correct the book count of a warehouse after a stock count."""
import money
import skus
import stock
import warehouses
from errors import CommandError


def cmd_adjust(w, cmd):
    cmd.allow()
    wh = warehouses.checked(cmd.arg(0))
    sku = cmd.arg(1)
    if not skus.known(sku):
        raise CommandError("unknown_sku", sku)
    delta = money.parse_signed(cmd.arg(2), 100000)
    lots = stock.lots_of(w, wh.CODE, sku)
    if not lots:
        raise CommandError("no_stock", sku, wh.CODE)
    if delta > 0:
        total = stock.total_units(w, wh.CODE)
        if not wh.accepts_units(total, delta):
            raise CommandError("over_capacity", wh.CODE, total, wh.limit())
        lot = max(lots, key=lambda x: (x.received, x.id))
        lot.qty += delta
        stock.record(w, "adjust", wh.CODE, sku, delta, ref=lot.id)
    else:
        need = -delta
        room = sum(stock.free(lot) for lot in lots)
        if need > room:
            raise CommandError("short_stock", room, sku, wh.CODE)
        for lot in lots:
            if need == 0:
                break
            take = min(lot.qty, need)
            if take == 0:
                continue
            lot.qty -= take
            need -= take
            stock.record(w, "adjust", wh.CODE, sku, -take, ref=lot.id)
            if lot.qty == 0:
                stock.remove_lot(w, lot)
    w.audit_add("adjust", wh.CODE, sku, delta)
    w.out.emit("adjusted %s %s by %+d, on hand %d" % (wh.CODE, sku, delta,
                                                      stock.on_hand(w, wh.CODE, sku)))
