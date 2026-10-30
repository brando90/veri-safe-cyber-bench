# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Report goods_region: Goods value ordered per destination region."""
import customers
import orders
import reportutil

NAME = "goods_region"
TITLE = "Goods value ordered per destination region"


def key_of(w, order):
    return customers.get(w, order.cust).region


def value_of(order):
    return order.goods


def total_orders(w):
    """Number of orders a report of this kind covers."""
    return len(orders.live(w))


def run(w, cmd):
    cmd.allow("cust")
    _, want_cust = reportutil.filters(w, cmd)
    rows = {}
    for order in orders.live(w):
        if want_cust and order.cust != want_cust:
            continue
        key = key_of(w, order)
        rows[key] = rows.get(key, 0) + value_of(order)
    reportutil.emit_groups(w, rows)


def describe():
    return "%s: %s" % (NAME, TITLE)
