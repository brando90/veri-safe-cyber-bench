# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""backorder run: give waiting orders the stock that has arrived since."""
import customers
import orders
import routing
import tiers


def waiting(w):
    return [o for o in orders.all_sorted(w) if any(line.backorder > 0 for line in o.lines)]


def cmd_run(w, cmd):
    cmd.allow()
    checked = filled = 0
    queue = sorted(waiting(w), key=lambda o: (tiers.rank(customers.get(w, o.cust).tier), o.number))
    for order in queue:
        cust = customers.get(w, order.cust)
        if cust.hold:
            continue
        checked += 1
        got = routing.allocate(w, order, cust)
        if got:
            filled += 1
            orders.refresh(order)
            w.out.emit("backorder %s allocated %d units, status %s" % (order.number, got, order.status))
    w.out.emit("%d orders checked, %d filled" % (checked, filled))
