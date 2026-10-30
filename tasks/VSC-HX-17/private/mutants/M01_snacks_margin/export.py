# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""export: dump orders, stock, shipments or the ledger as CSV or TSV text."""
import orders
from errors import CommandError


def cell(text, sep):
    text = str(text)
    if sep == ",":
        if any(c in text for c in ',"\n'):
            return '"' + text.replace('"', '""') + '"'
        return text
    return text.replace("\t", " ").replace("\n", " ")


def rows_orders(w):
    yield ("number", "customer", "day", "goods", "status")
    for o in orders.all_sorted(w):
        yield (o.number, o.cust, o.day, o.goods, o.status)


def rows_stock(w):
    yield ("lot", "warehouse", "sku", "qty", "reserved", "expiry")
    for lot in sorted(w.lots.values(), key=lambda x: x.id):
        yield (lot.id, lot.wh, lot.sku, lot.qty, lot.reserved, "" if lot.expiry is None else lot.expiry)


def rows_shipments(w):
    yield ("id", "order", "warehouse", "carrier", "weight", "goods", "freight", "handling", "duty", "eta")
    for s in w.shipments:
        yield (s.id, s.order, s.wh, s.carrier, s.weight, s.goods, s.freight, s.handling, s.duty, s.eta)


def rows_ledger(w):
    yield ("seq", "day", "kind", "warehouse", "sku", "delta", "qty", "ref")
    for m in w.moves:
        yield (m.seq, m.day, m.kind, m.wh, m.sku, m.delta, m.qty, m.ref)


KINDS = {"orders": rows_orders, "stock": rows_stock, "shipments": rows_shipments,
         "ledger": rows_ledger}
FORMATS = {"csv": ",", "tsv": "\t"}


def cmd_export(w, cmd):
    cmd.allow()
    kind, fmt = cmd.arg(0), cmd.arg(1)
    if kind not in KINDS:
        raise CommandError("unknown_export", kind)
    if fmt not in FORMATS:
        raise CommandError("unknown_format", fmt)
    sep = FORMATS[fmt]
    for row in KINDS[kind](w):
        w.out.emit(sep.join(cell(c, sep) for c in row))
