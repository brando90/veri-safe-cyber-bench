# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""set exempt: change the exempt of a customer."""
import customers
from errors import CommandError


def check(w, cust, text):
    """The new value for TEXT, or an error."""
    if text not in ("yes", "no"):
        raise CommandError("bad_yesno", text)
    value = text == "yes"
    return value


def cmd_set_exempt(w, cmd):
    cust = customers.open(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = cust.exempt
    if value == old:
        w.out.emit("customer %s exempt unchanged" % cust.id)
        return
    cust.exempt = value
    w.audit_add("set exempt", cust.id, old, value)
    w.out.emit("customer %s exempt %s" % (cust.id, "yes" if value else "no"))
