# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""void: cancel an invoice that has no payments held against it."""
import invoice
import ledger
from errors import CommandError


def cmd_void(w, cmd):
    inv = invoice.find(w, cmd.arg(0))
    if inv.status == "void":
        raise CommandError("voided", inv.number)
    if inv.paid - inv.refunded > 0:
        raise CommandError("has_payments", inv.number)
    inv.status = "void"
    ledger.post(w, "void", inv.cust, inv.number, inv.total)
    w.audit_add("void", inv.number)
    w.out.emit("void %s" % inv.number)
