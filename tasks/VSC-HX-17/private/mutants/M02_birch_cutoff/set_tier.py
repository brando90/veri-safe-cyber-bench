# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""set tier: change the tier of a customer."""
import customers
import tiers
from errors import CommandError


def show(value):
    return value


def check(w, cust, text):
    """The new value for TEXT, or an error."""
    value = tiers.check(text)
    return value


def cmd_set_tier(w, cmd):
    cmd.allow()
    cust = customers.open(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = cust.tier
    if value == old:
        w.out.emit("customer %s tier unchanged" % cust.id)
        return
    cust.tier = value
    w.audit_add("set tier", cust.id, show(old), show(value))
    w.out.emit("customer %s tier %s" % (cust.id, show(value)))
