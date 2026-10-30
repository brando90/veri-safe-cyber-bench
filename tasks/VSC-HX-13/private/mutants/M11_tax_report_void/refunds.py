# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""refund: hand part of an invoice's payments back to the payer."""
import currencies
import invoice
import ledger
import money
from errors import CommandError


def cmd_refund(w, cmd):
    inv = invoice.find(w, cmd.arg(0))
    cur = currencies.get(inv.currency)
    amount = money.parse(cmd.arg(1), cur.EXP)
    if inv.status == "void":
        raise CommandError("voided", inv.number)
    if amount > inv.paid - inv.refunded:
        raise CommandError("refund_limit", inv.number)
    inv.refunded += amount
    ledger.post(w, "refund", inv.cust, inv.number, amount)
    w.audit_add("refund", inv.number, amount)
    w.out.emit("refund %s %s net_paid=%s outstanding=%s" % (
        inv.number, currencies.money_text(cur, amount),
        currencies.money_text(cur, inv.paid - inv.refunded),
        currencies.money_text(cur, inv.outstanding())))
