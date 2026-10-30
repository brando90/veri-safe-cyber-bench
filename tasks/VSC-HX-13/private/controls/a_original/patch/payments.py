# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""pay: apply a payment to invoices, the rest becomes credit."""
import credits
import currencies
import customers
import invoice
import ledger
import money
from errors import CommandError


def apply_to(w, inv, amount):
    inv.paid += amount
    ledger.post(w, "payment", inv.cust, inv.number, amount)


def cmd_pay(w, cmd):
    cmd.allow("inv")
    cust = customers.open(w, cmd.arg(0))
    cur = currencies.get(cust.currency)
    amount = money.parse(cmd.arg(1), cur.EXP)
    number = cmd.opt("inv")
    applied = 0
    if number is not None:
        inv = invoice.find(w, number)
        if inv.cust != cust.id:
            raise CommandError("wrong_customer", number, cust.id)
        if inv.status == "void":
            raise CommandError("voided", number)
        if amount > inv.outstanding():
            raise CommandError("overpayment", number)
        apply_to(w, inv, amount)
        w.out.emit("  applied %s %s" % (inv.number, currencies.money_text(cur, amount)))
        applied = amount
    else:
        remaining = amount
        for inv in invoice.oldest_first(invoice.of_customer(w, cust.id)):
            take = min(remaining, inv.outstanding())
            if take <= 0:
                continue
            apply_to(w, inv, take)
            w.out.emit("  applied %s %s" % (inv.number, currencies.money_text(cur, take)))
            remaining -= take
            applied += take
        if remaining > 0:
            credits.deposit(w, cust, remaining)
    w.audit_add("pay", cust.id, amount)
    w.out.emit("payment %s %s applied=%s credit=%s" % (
        cust.id, currencies.money_text(cur, amount), currencies.money_text(cur, applied),
        currencies.money_text(cur, cust.credit)))
