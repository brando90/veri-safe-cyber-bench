# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Report goods_tier: Goods value ordered per customer tier."""
import customers
import orders
import reportutil

NAME = "goods_tier"
TITLE = "Goods value ordered per customer tier"


def key_of(w, order):
    return customers.get(w, order.cust).tier


def value_of(order):
    return order.goods


def total_orders(w):
    """Number of orders a report of this kind covers."""
    return len(orders.live(w))


def run(w, cmd):
    cmd.allow("cust")
    _, want_cust = reportutil.filters(w, cmd)
    rows = {}
    for order in w.orders.values():
        if want_cust and order.cust != want_cust:
            continue
        key = key_of(w, order)
        rows[key] = rows.get(key, 0) + value_of(order)
    reportutil.emit_groups(w, rows)


def describe():
    return "%s: %s" % (NAME, TITLE)
