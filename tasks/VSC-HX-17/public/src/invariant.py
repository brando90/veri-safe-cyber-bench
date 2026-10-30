# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The program's own consistency check, run after every command.

A violation is reported as INVARIANT: on standard error and ends the run
with exit status 86.
"""
import orders
from errors import InvariantViolation


def fail(msg, *params):
    raise InvariantViolation(msg % params)


def check_lots(w):
    for lot in w.lots.values():
        if lot.qty <= 0:
            fail("lot %s holds %d units", lot.id, lot.qty)
        if not 0 <= lot.reserved <= lot.qty:
            fail("lot %s has %d units reserved of %d", lot.id, lot.reserved, lot.qty)
        if lot.id not in w.by_slot.get((lot.wh, lot.sku), ()):
            fail("lot %s is missing from its slot", lot.id)


def check_ledger(w):
    booked = {}
    for m in w.moves:
        booked[(m.wh, m.sku)] = booked.get((m.wh, m.sku), 0) + m.delta
    held = {}
    for lot in w.lots.values():
        held[(lot.wh, lot.sku)] = held.get((lot.wh, lot.sku), 0) + lot.qty
    for key in sorted(set(booked) | set(held)):
        if booked.get(key, 0) != held.get(key, 0):
            fail("%s %s: ledger says %d units, lots hold %d", key[0], key[1],
                 booked.get(key, 0), held.get(key, 0))


def check_orders(w):
    reserved = {}
    for order in w.orders.values():
        for line in order.lines:
            if min(line.backorder, line.shipped, line.returned, line.cancelled) < 0:
                fail("%s %s: negative quantity", order.number, line.sku)
            if line.qty != line.allocated() + line.backorder + line.shipped + line.cancelled:
                fail("%s %s: quantities do not add up to %d", order.number, line.sku, line.qty)
            if line.returned > line.shipped:
                fail("%s %s: returned %d exceeds shipped %d", order.number, line.sku,
                     line.returned, line.shipped)
            for wh, lot_id, qty in line.allocs:
                lot = w.lots.get(lot_id)
                if lot is None or lot.wh != wh or lot.sku != line.sku:
                    fail("%s %s: allocation on a missing lot %s", order.number, line.sku, lot_id)
                reserved[lot_id] = reserved.get(lot_id, 0) + qty
        if order.status != orders.status_of(order):
            fail("%s: status %s does not match its lines", order.number, order.status)
    for lot in w.lots.values():
        if reserved.get(lot.id, 0) != lot.reserved:
            fail("lot %s: %d units reserved but %d allocated", lot.id, lot.reserved,
                 reserved.get(lot.id, 0))


def check_shipments(w):
    shipped = {}
    for n, s in enumerate(w.shipments, 1):
        if s.id != "SHP-%04d" % n:
            fail("shipment %s is out of sequence", s.id)
        if min(s.weight, s.goods, s.freight, s.handling, s.duty) < 0:
            fail("shipment %s has a negative amount", s.id)
        if s.eta < s.ship_day:
            fail("shipment %s arrives before it leaves", s.id)
        for sku, qty in s.lines:
            shipped[(s.order, sku)] = shipped.get((s.order, sku), 0) + qty
    for order in w.orders.values():
        for line in order.lines:
            if shipped.get((order.number, line.sku), 0) != line.shipped:
                fail("%s %s: shipments carry %d units but %d are marked shipped", order.number,
                     line.sku, shipped.get((order.number, line.sku), 0), line.shipped)


def full_check(w):
    check_lots(w)
    check_ledger(w)
    check_orders(w)
    check_shipments(w)
