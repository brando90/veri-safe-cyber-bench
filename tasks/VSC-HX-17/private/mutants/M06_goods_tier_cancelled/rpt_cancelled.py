# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Report cancelled: Orders that were cancelled."""
import money
import orders
import reportutil

NAME = "cancelled"
TITLE = "Orders that were cancelled"


def run(w, cmd):
    cmd.allow("cust")
    _, want_cust = reportutil.filters(w, cmd)
    count = 0
    for order in w.orders.values():
        if order.status != "cancelled":
            continue
        if want_cust and order.cust != want_cust:
            continue
        w.out.emit("  %s %s day %d goods %s" % (order.number, order.cust, order.day,
                                                money.fmt(order.goods)))
        count += 1
    w.out.emit("  %d cancelled" % count)
