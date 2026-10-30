# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""set region: change the region of a customer."""
import customers
import taxes
from errors import CommandError


def check(w, cust, text):
    """The new value for TEXT, or an error."""
    if not taxes.known(text):
        raise CommandError("unknown_region", text)
    value = text
    return value


def cmd_set_region(w, cmd):
    cust = customers.open(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = cust.region
    if value == old:
        w.out.emit("customer %s region unchanged" % cust.id)
        return
    cust.region = value
    w.audit_add("set region", cust.id, old, value)
    w.out.emit("customer %s region %s" % (cust.id, value))
