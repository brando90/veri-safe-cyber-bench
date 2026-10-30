# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Report top: Customers ranked by net revenue in one currency."""
import currencies
import invoice
import money
from errors import CommandError

NAME = "top"
TITLE = "Customers ranked by net revenue in one currency"


def run(w, cmd):
    code = cmd.arg(1)
    if not currencies.known(code):
        raise CommandError("unknown_currency", code)
    limit = money.parse_int(cmd.arg(2, "5"), 1, 100)
    cur = currencies.get(code)
    totals = {}
    for inv in invoice.live(w):
        if inv.currency != code:
            continue
        net = inv.subtotal - inv.discount + inv.late
        totals[inv.cust] = totals.get(inv.cust, 0) + net
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:limit]
    for rank, (cid, net) in enumerate(ranked, 1):
        w.out.emit("  %d %s %s" % (rank, cid, currencies.money_text(cur, net)))
    if not ranked:
        w.out.emit("  (none)")
