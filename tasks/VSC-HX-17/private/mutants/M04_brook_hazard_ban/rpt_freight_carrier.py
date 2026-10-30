# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Report freight_carrier: Freight charged per carrier."""
import customers
import orders
import reportutil

NAME = "freight_carrier"
TITLE = "Freight charged per carrier"


def key_of(shipment):
    return shipment.carrier


def value_of(shipment):
    return shipment.freight


def run(w, cmd):
    cmd.allow("wh", "cust")
    want_wh, want_cust = reportutil.filters(w, cmd)
    rows = {}
    for s in w.shipments:
        if want_wh and s.wh != want_wh:
            continue
        if want_cust and orders.find(w, s.order).cust != want_cust:
            continue
        amount = value_of(s)
        if amount == 0:
            continue
        rows[key_of(s)] = rows.get(key_of(s), 0) + amount
    reportutil.emit_groups(w, rows)


def describe():
    return "%s: %s" % (NAME, TITLE)
