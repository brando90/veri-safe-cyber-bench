# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""set split: change the split of a customer."""
import customers
from errors import CommandError


def show(value):
    return "yes" if value else "no"


def check(w, cust, text):
    """The new value for TEXT, or an error."""
    if text not in ("yes", "no"):
        raise CommandError("bad_yesno", text)
    value = text == "yes"
    return value


def cmd_set_split(w, cmd):
    cmd.allow()
    cust = customers.open(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = cust.split
    if value == old:
        w.out.emit("customer %s split unchanged" % cust.id)
        return
    cust.split = value
    w.audit_add("set split", cust.id, show(old), show(value))
    w.out.emit("customer %s split %s" % (cust.id, show(value)))
