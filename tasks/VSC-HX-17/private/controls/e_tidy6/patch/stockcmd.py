# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""stock and ledger: listings of the lots and of every stock movement."""
import stock
import warehouses
from errors import CommandError


def cmd_stock(w, cmd):
    cmd.allow("sku")
    code = cmd.arg(0, "")
    if code:
        warehouses.checked(code)
    want = cmd.opt("sku")
    lots = units = 0
    for lot in sorted(w.lots.values(), key=lambda x: (x.wh, x.sku, x.id)):
        if code and lot.wh != code:
            continue
        if want and lot.sku != want:
            continue
        w.out.emit("  %s %s %s qty=%d reserved=%d expiry=%s received=%d" % (
            lot.id, lot.wh, lot.sku, lot.qty, lot.reserved,
            "-" if lot.expiry is None else lot.expiry, lot.received))
        lots += 1
        units += lot.qty
    w.out.emit("%d lots, %d units" % (lots, units))


def cmd_ledger(w, cmd):
    cmd.allow("kind", "sku")
    code = cmd.arg(0, "")
    if code:
        warehouses.checked(code)
    kind = cmd.opt("kind")
    want = cmd.opt("sku")
    count = 0
    for m in w.moves:
        if code and m.wh != code:
            continue
        if kind and m.kind != kind:
            continue
        if want and m.sku != want:
            continue
        w.out.emit("  #%d day %d %s %s %s %+d %s" % (m.seq, m.day, m.kind, m.wh, m.sku, m.delta, m.ref or "-"))
        count += 1
    w.out.emit("%d movements" % count)
