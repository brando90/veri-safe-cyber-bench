# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""set phone: change the phone of a customer."""
import re

import customers
import output
from errors import CommandError

PATTERN = r"[0-9+() -]{3,20}"


def check(w, cust, text):
    """The new value for TEXT, or an error."""
    if text == "-":
        value = ""
    elif not re.fullmatch(PATTERN, text):
        raise CommandError("bad_value", text)
    else:
        value = text
    return value


def cmd_set_phone(w, cmd):
    cust = customers.get(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = cust.phone
    if value == old:
        w.out.emit("customer %s phone unchanged" % cust.id)
        return
    cust.phone = value
    w.audit_add("set phone", cust.id, old, value)
    w.out.emit("customer %s phone %s" % (cust.id, output.dash(value)))
