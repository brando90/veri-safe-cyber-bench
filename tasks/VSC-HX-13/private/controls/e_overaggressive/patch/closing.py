# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""customer close: retire a customer whose invoices are all settled."""
import credits
import customers
import invoice
from errors import CommandError


def cmd_close(w, cmd):
    cust = customers.get(w, cmd.arg(0))
    if cust.closed:
        raise CommandError("already_closed", cust.id)
    if any(inv.outstanding() > 0 for inv in invoice.of_customer(w, cust.id)):
        raise CommandError("open_invoices", cust.id)
    credits.forfeit(w, cust)
    cust.closed = True
    w.audit_add("customer close", cust.id)
    w.out.emit("customer %s closed" % cust.id)
