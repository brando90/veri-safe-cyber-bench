# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Shared output of the reports: grouped rows with a total."""
import customers
import money
import warehouses


def fmt_value(kind, amount):
    return money.fmt(amount) if kind == "money" else "%d" % amount


def emit_groups(w, rows, kind="money", order=None):
    """ROWS maps a key to an amount; print them sorted, then one total line."""
    if order is None:
        keys = sorted(rows)
    else:
        keys = sorted(rows, key=lambda k: (order.index(k), k))
    total = 0
    for key in keys:
        w.out.emit("  %s %s" % (key, fmt_value(kind, rows[key])))
        total += rows[key]
    if not rows:
        w.out.emit("  (none)")
    w.out.emit("  total %s" % fmt_value(kind, total))


def filters(w, cmd):
    """The wh= and cust= options of a report, checked: (warehouse, customer id)."""
    want_wh = cmd.opt("wh")
    want_cust = cmd.opt("cust")
    if want_wh is not None:
        warehouses.checked(want_wh)
    if want_cust is not None:
        customers.get(w, want_cust)
    return want_wh, want_cust
