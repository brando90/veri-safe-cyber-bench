# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""set email: change the email of a customer."""
import customers
import output
from errors import CommandError

MAX_LEN = 60


def show(value):
    return output.dash(value)


def check(w, cust, text):
    """The new value for TEXT, or an error."""
    if text == "-":
        value = ""
    elif "@" not in text or len(text) > MAX_LEN:
        raise CommandError("bad_value", text)
    else:
        value = text
    return value


def cmd_set_email(w, cmd):
    cmd.allow()
    cust = customers.get(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = cust.email
    if value == old:
        w.out.emit("customer %s email unchanged" % cust.id)
        return
    cust.email = value
    w.audit_add("set email", cust.id, show(old), show(value))
    w.out.emit("customer %s email %s" % (cust.id, show(value)))
