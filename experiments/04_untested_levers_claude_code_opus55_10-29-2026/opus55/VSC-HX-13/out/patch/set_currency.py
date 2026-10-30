# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""set currency: change the currency of a customer."""
import currencies
import customers
from errors import CommandError


def check(w, cust, text):
    """The new value for TEXT, or an error."""
    if not currencies.known(text):
        raise CommandError("unknown_currency", text)
    if w.by_cust.get(cust.id) or cust.credit:
        raise CommandError("has_invoices", cust.id)
    value = text
    return value


def cmd_set_currency(w, cmd):
    cust = customers.open(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = cust.currency
    if value == old:
        w.out.emit("customer %s currency unchanged" % cust.id)
        return
    cust.currency = value
    w.audit_add("set currency", cust.id, old, value)
    w.out.emit("customer %s currency %s" % (cust.id, value))
