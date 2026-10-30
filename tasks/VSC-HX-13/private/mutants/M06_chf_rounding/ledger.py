# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The ledger: every movement of money, in order."""
import currencies
import customers


class Entry:
    def __init__(self, seq, day, kind, cust, inv, amount):
        self.seq = seq
        self.day = day
        self.kind = kind
        self.cust = cust
        self.inv = inv
        self.amount = amount


def post(w, kind, cust_id, inv_number, amount):
    w.ledger.append(Entry(len(w.ledger) + 1, w.day, kind, cust_id, inv_number, amount))
    if kind == "credit_in":
        w.credit_sum[cust_id] = w.credit_sum.get(cust_id, 0) + amount
    elif kind == "credit_use":
        w.credit_sum[cust_id] = w.credit_sum.get(cust_id, 0) - amount


def cmd_ledger(w, cmd):
    cmd.allow("kind")
    cid = cmd.arg(0, "")
    if cid:
        customers.get(w, cid)
    shown = 0
    for e in w.ledger:
        if cid and e.cust != cid:
            continue
        if cmd.opt("kind") not in (None, e.kind):
            continue
        cur = currencies.get(w.customers[e.cust].currency)
        w.out.emit("%d day=%d %s %s %s %s" % (
            e.seq, e.day, e.kind, e.cust, e.inv, currencies.money_text(cur, e.amount)))
        shown += 1
    w.out.emit("%d entries" % shown)
