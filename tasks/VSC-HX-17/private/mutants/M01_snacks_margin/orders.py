# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Orders: creation, listing, cancelling and the status of an order."""
import re

import customers
import money
import output
import regions
import routing
import skus
import stock
from errors import CommandError
from model import Line, Order

LINE_RE = re.compile(r"([a-z0-9-]+):([1-9][0-9]{0,8})")
REF_RE = re.compile(r"[A-Za-z0-9._-]{1,30}")


def find(w, number):
    order = w.orders.get(number)
    if order is None:
        raise CommandError("unknown_order", number)
    return order


def all_sorted(w):
    return [w.orders[k] for k in sorted(w.orders)]


def live(w):
    """Orders that are not cancelled, by number."""
    return [o for o in all_sorted(w) if o.status != "cancelled"]


def status_of(order):
    pending = sum(line.pending() for line in order.lines)
    alloc = sum(line.allocated() for line in order.lines)
    shipped = sum(line.shipped for line in order.lines)
    if pending == 0:
        return "shipped" if shipped else "cancelled"
    if pending == alloc:
        return "open"
    if alloc == 0 and shipped == 0:
        return "backorder"
    return "partial"


def refresh(order):
    order.status = status_of(order)


def parse_lines(args):
    """(sku, qty) pairs from SKU:QTY words; repeated SKUs are added up."""
    merged = {}
    for text in args:
        m = LINE_RE.fullmatch(text)
        if m is None:
            raise CommandError("bad_line", text)
        sku = m.group(1)
        if not skus.known(sku):
            raise CommandError("unknown_sku", sku)
        merged[sku] = merged.get(sku, 0) + int(m.group(2))
    return list(merged.items())


def cmd_add(w, cmd):
    cmd.allow("ref")
    cust = customers.open(w, cmd.arg(0))
    if cust.hold:
        raise CommandError("on_hold", cust.id)
    pairs = parse_lines(cmd.args[1:])
    if not pairs:
        raise CommandError("usage", cmd.usage)
    region = regions.get(cust.region)
    goods = 0
    for sku, qty in pairs:
        cat = stock.category_of(sku)
        cat.check_line(qty)
        if not region.allows(cat.HAZ):
            raise CommandError("restricted", region.CODE, cat.HAZ, sku)
        goods += skus.price(sku) * qty
    ref = cmd.opt("ref", "")
    if ref:
        if not REF_RE.fullmatch(ref):
            raise CommandError("bad_value", ref)
        if (cust.id, ref) in w.order_refs:
            raise CommandError("duplicate_ref", ref)
    number = "ORD-%04d" % (len(w.orders) + 1)
    order = Order(number, cust.id, w.day, [Line(s, q, backorder=q) for s, q in pairs], goods, ref)
    w.orders[number] = order
    if ref:
        w.order_refs[(cust.id, ref)] = number
    routing.allocate(w, order, cust)
    refresh(order)
    w.audit_add("order add", cust.id, number, goods)
    w.out.emit("order %s customer %s goods %s status %s" % (
        number, cust.id, money.fmt(goods), order.status))
    for line in order.lines:
        w.out.emit("  %s qty=%d allocated=%d backorder=%d" % (
            line.sku, line.qty, line.allocated(), line.backorder))


def cmd_show(w, cmd):
    order = find(w, cmd.arg(0))
    w.out.emit("order %s customer %s day %d goods %s status %s ref=%s" % (
        order.number, order.cust, order.day, money.fmt(order.goods), order.status,
        output.dash(order.ref)))
    for line in order.lines:
        w.out.emit("  %s qty=%d allocated=%d backorder=%d shipped=%d returned=%d cancelled=%d" % (
            line.sku, line.qty, line.allocated(), line.backorder, line.shipped,
            line.returned, line.cancelled))
        for wh, lot_id, qty in line.allocs:
            w.out.emit("    from %s lot %s x%d" % (wh, lot_id, qty))


def cmd_list(w, cmd):
    cmd.allow("state")
    want = cmd.arg(0, "") if cmd.args else ""
    state = cmd.opt("state")
    count = 0
    for order in all_sorted(w):
        if want and order.cust != want:
            continue
        if state and order.status != state:
            continue
        w.out.emit("%s %s day %d %s %s" % (order.number, order.cust, order.day,
                                           money.fmt(order.goods), order.status))
        count += 1
    w.out.emit("%d orders" % count)


def cmd_cancel(w, cmd):
    order = find(w, cmd.arg(0))
    if sum(line.pending() for line in order.lines) == 0:
        raise CommandError("nothing_pending", order.number)
    units = 0
    for line in order.lines:
        stock.release(w, line.allocs)
        units += line.pending()
        line.cancelled += line.pending()
        line.allocs = []
        line.backorder = 0
    order.cancelled = not any(line.shipped for line in order.lines)
    refresh(order)
    w.audit_add("order cancel", order.cust, order.number, units)
    w.out.emit("order %s cancelled %d units, status %s" % (order.number, units, order.status))
