# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""receive: book incoming stock into a warehouse as a new lot."""
import money
import skus
import stock
import warehouses
from errors import CommandError


def cmd_receive(w, cmd):
    cmd.allow("exp")
    wh = warehouses.checked(cmd.arg(0))
    sku = cmd.arg(1)
    if not skus.known(sku):
        raise CommandError("unknown_sku", sku)
    cat = stock.category_of(sku)
    if not wh.can_store(cat):
        raise CommandError("not_stocked", wh.CODE, sku)
    units = cat.round_receive(money.parse_int(cmd.arg(2), 1, 100000))
    total = stock.total_units(w, wh.CODE)
    if not wh.accepts_units(total, units):
        raise CommandError("over_capacity", wh.CODE, total, wh.limit())
    expiry = cat.expiry_for(w.day, cmd.opt("exp"))
    lot = stock.new_lot(w, wh.CODE, sku, units, expiry)
    stock.record(w, "receive", wh.CODE, sku, units, ref=lot.id)
    w.audit_add("receive", wh.CODE, sku, units)
    w.out.emit("received lot %s %s %s units %d expiry %s" % (
        lot.id, wh.CODE, sku, units, "-" if expiry is None else expiry))
