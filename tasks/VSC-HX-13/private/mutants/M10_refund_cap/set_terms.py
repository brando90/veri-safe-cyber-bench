# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""set terms: change the terms of a customer."""
import customers
import money
from errors import CommandError

MIN_DAYS = 1
MAX_DAYS = 120


def check(w, cust, text):
    """The new value for TEXT, or an error."""
    value = money.parse_int(text, MIN_DAYS, MAX_DAYS)
    return value


def cmd_set_terms(w, cmd):
    cust = customers.open(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = cust.terms
    if value == old:
        w.out.emit("customer %s terms unchanged" % cust.id)
        return
    cust.terms = value
    w.audit_add("set terms", cust.id, old, value)
    w.out.emit("customer %s terms %s" % (cust.id, value))
