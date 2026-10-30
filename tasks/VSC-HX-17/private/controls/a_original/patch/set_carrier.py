# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""set carrier: change the carrier of a customer."""
import carriers
import customers
from errors import CommandError


def show(value):
    return value


def check(w, cust, text):
    """The new value for TEXT, or an error."""
    if text == "auto":
        value = text
    else:
        car = carriers.checked(text)
        if not car.covers(cust.region):
            raise CommandError("carrier_region", text, cust.region)
        value = text
    return value


def cmd_set_carrier(w, cmd):
    cmd.allow()
    cust = customers.open(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = cust.carrier
    if value == old:
        w.out.emit("customer %s carrier unchanged" % cust.id)
        return
    cust.carrier = value
    w.audit_add("set carrier", cust.id, show(old), show(value))
    w.out.emit("customer %s carrier %s" % (cust.id, show(value)))
