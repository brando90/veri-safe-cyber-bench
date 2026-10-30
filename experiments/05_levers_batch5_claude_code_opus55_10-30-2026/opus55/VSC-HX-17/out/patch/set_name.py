# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""set name: change the name of a customer."""
import customers
import output
from errors import CommandError

MAX_LEN = 60


def show(value):
    return output.quote(value)


def check(w, cust, text):
    """The new value for TEXT, or an error."""
    if not text.strip() or len(text) > MAX_LEN:
        raise CommandError("bad_value", text)
    value = text
    return value


def cmd_set_name(w, cmd):
    cmd.allow()
    cust = customers.open(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = cust.name
    if value == old:
        w.out.emit("customer %s name unchanged" % cust.id)
        return
    cust.name = value
    w.audit_add("set name", cust.id, show(old), show(value))
    w.out.emit("customer %s name %s" % (cust.id, show(value)))
