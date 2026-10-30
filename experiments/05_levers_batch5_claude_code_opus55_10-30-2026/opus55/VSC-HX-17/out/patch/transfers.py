# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""transfer: move free stock from one warehouse to another."""
import money
import skus
import stock
import warehouses
from errors import CommandError


def cmd_transfer(w, cmd):
    cmd.allow()
    src = warehouses.checked(cmd.arg(0))
    dst = warehouses.checked(cmd.arg(1))
    if src.CODE == dst.CODE:
        raise CommandError("same_warehouse", src.CODE)
    sku = cmd.arg(2)
    if not skus.known(sku):
        raise CommandError("unknown_sku", sku)
    units = money.parse_int(cmd.arg(3), 1, 100000)
    cat = stock.category_of(sku)
    if not dst.can_store(cat):
        raise CommandError("not_stocked", dst.CODE, sku)
    movable = [lot for lot in stock.lots_of(w, src.CODE, sku)
               if stock.free(lot) > 0 and not cat.is_expired(lot.expiry, w.day)]
    room = sum(stock.free(lot) for lot in movable)
    if units > room:
        raise CommandError("short_stock", room, sku, src.CODE)
    left = units
    for lot in movable:
        if left == 0:
            break
        take = min(stock.free(lot), left)
        stock.new_lot(w, dst.CODE, sku, take, lot.expiry)
        lot.qty -= take
        left -= take
        stock.record(w, "transfer_out", src.CODE, sku, -take, ref=dst.CODE)
        stock.record(w, "transfer_in", dst.CODE, sku, take, ref=src.CODE)
        if lot.qty == 0:
            stock.remove_lot(w, lot)
    w.audit_add("transfer", src.CODE, sku, units, dst.CODE)
    w.out.emit("transferred %d %s from %s to %s" % (units, sku, src.CODE, dst.CODE))
