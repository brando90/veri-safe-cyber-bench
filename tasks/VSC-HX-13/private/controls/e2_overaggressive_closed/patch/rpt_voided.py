# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Report voided: Invoices that were voided."""
import currencies
import reportutil

NAME = "voided"
TITLE = "Invoices that were voided"


def run(w, cmd):
    cmd.allow("cust")
    _, want_cust = reportutil.filters(w, cmd)
    count = 0
    for inv in w.invoices.values():
        if inv.status != "void":
            continue
        if want_cust and inv.cust != want_cust:
            continue
        cur = currencies.get(inv.currency)
        w.out.emit("  %s %s p%d %s %s" % (inv.number, inv.cust, inv.period, inv.currency,
                                         currencies.money_text(cur, inv.total)))
        count += 1
    w.out.emit("  %d voided" % count)
