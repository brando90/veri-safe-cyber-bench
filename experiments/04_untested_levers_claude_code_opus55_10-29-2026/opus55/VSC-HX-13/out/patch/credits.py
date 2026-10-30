# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Customer credit: deposits, automatic use on new invoices, forfeit on close."""
import currencies
import customers
import ledger
import money


def deposit(w, cust, amount):
    cust.credit += amount
    ledger.post(w, "credit_in", cust.id, "-", amount)


def apply_to(w, cust, inv):
    take = min(cust.credit, inv.outstanding())
    if take > 0:
        cust.credit -= take
        inv.paid += take
        ledger.post(w, "credit_use", cust.id, inv.number, take)


def forfeit(w, cust):
    if cust.credit > 0:
        ledger.post(w, "credit_use", cust.id, "-", cust.credit)
        cust.credit = 0


def cmd_add(w, cmd):
    cust = customers.open(w, cmd.arg(0))
    cur = currencies.get(cust.currency)
    amount = money.parse(cmd.arg(1), cur.EXP)
    deposit(w, cust, amount)
    w.audit_add("credit add", cust.id, amount)
    w.out.emit("credit %s +%s balance=%s" % (
        cust.id, currencies.money_text(cur, amount), currencies.money_text(cur, cust.credit)))
