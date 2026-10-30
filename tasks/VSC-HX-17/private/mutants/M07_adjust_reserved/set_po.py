# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""set po: change the po of a customer."""
import customers
import output
from errors import CommandError

MAX_LEN = 40


def show(value):
    return output.dash(value)


def check(w, cust, text):
    """The new value for TEXT, or an error."""
    if len(text) > MAX_LEN or any(ord(c) < 32 for c in text):
        raise CommandError("bad_value", text)
    value = "" if text == "-" else text
    return value


def cmd_set_po(w, cmd):
    cmd.allow()
    cust = customers.open(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = cust.po
    if value == old:
        w.out.emit("customer %s po unchanged" % cust.id)
        return
    cust.po = value
    w.audit_add("set po", cust.id, show(old), show(value))
    w.out.emit("customer %s po %s" % (cust.id, show(value)))
