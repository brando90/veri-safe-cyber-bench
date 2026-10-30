# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""statement: one customer's invoices and balance."""
import currencies
import customers
import invoice
import money


def cmd_statement(w, cmd):
    cmd.allow("period")
    cust = customers.open(w, cmd.arg(0))
    want = cmd.opt("period")
    if want is not None:
        want = money.parse_int(want, 0, 100000)
    cur = currencies.get(cust.currency)
    text = lambda amount: currencies.money_text(cur, amount)  # noqa: E731
    w.out.emit("statement %s %s" % (cust.id, cust.currency))
    owed = 0
    for inv in invoice.of_customer(w, cust.id):
        if want is not None and inv.period != want:
            continue
        owed += inv.outstanding()
        w.out.emit("  %s p%d total=%s paid=%s refunded=%s outstanding=%s" % (
            inv.number, inv.period, text(inv.total), text(inv.paid), text(inv.refunded),
            text(inv.outstanding())))
    w.out.emit("  owed=%s credit=%s" % (text(owed), text(cust.credit)))
