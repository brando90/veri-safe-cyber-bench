# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""set note: change the note of a customer."""
import customers
import output
from errors import CommandError

MAX_LEN = 80


def show(value):
    return output.dash(value)


def check(w, cust, text):
    """The new value for TEXT, or an error."""
    if len(text) > MAX_LEN:
        raise CommandError("bad_value", text)
    value = "" if text == "-" else text
    return value


def cmd_set_note(w, cmd):
    cmd.allow()
    cust = customers.get(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = cust.note
    if value == old:
        w.out.emit("customer %s note unchanged" % cust.id)
        return
    cust.note = value
    w.out.emit("customer %s note %s" % (cust.id, show(value)))
