# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Shared output of the reports: grouped rows and a total per currency."""
import currencies
import customers
from errors import CommandError


def emit_groups(w, rows, order=None):
    """ROWS maps (key, currency) to an amount; print them sorted, then one
    total line per currency."""
    totals = {}
    if order is None:
        keys = sorted(rows)
    else:
        keys = sorted(rows, key=lambda k: (order.index(k[0]), k[1]))
    for key, code in keys:
        amount = rows[(key, code)]
        cur = currencies.get(code)
        w.out.emit("  %s %s %s" % (key, code, currencies.money_text(cur, amount)))
        totals[code] = totals.get(code, 0) + amount
    if not rows:
        w.out.emit("  (none)")
    for code in sorted(totals):
        w.out.emit("  total %s %s" % (code, currencies.money_text(currencies.get(code), totals[code])))


def filters(w, cmd):
    """The cur= and cust= options of a report, checked: (currency, customer id)."""
    want_cur = cmd.opt("cur")
    want_cust = cmd.opt("cust")
    if want_cur is not None and not currencies.known(want_cur):
        raise CommandError("unknown_currency", want_cur)
    if want_cust is not None:
        customers.get(w, want_cust)
    return want_cur, want_cust
