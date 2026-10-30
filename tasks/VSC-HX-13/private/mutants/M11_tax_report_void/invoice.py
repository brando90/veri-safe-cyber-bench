# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Invoice records, lookups shared by the commands, and invoice show / list."""
import currencies
import customers
import money
from errors import CommandError


class Line:
    def __init__(self, kind, desc, amount, tag):
        self.kind = kind
        self.desc = desc
        self.amount = amount
        self.tag = tag


class Invoice:
    def __init__(self, number, cust, period, issued, due, currency, region, plan, exempt):
        self.number = number
        self.cust = cust
        self.period = period
        self.issued = issued
        self.due = due
        self.currency = currency
        self.region = region
        self.plan = plan
        self.exempt = exempt
        self.lines = []
        self.discounts = []
        self.subtotal = 0
        self.discount = 0
        self.tax = 0
        self.late = 0
        self.total = 0
        self.paid = 0
        self.refunded = 0
        self.status = "open"
        self.late_day = None

    def outstanding(self):
        return self.total - (self.paid - self.refunded)


def state(inv):
    if inv.status == "void":
        return "void"
    return "paid" if inv.outstanding() == 0 else "open"


def find(w, number):
    inv = w.invoices.get(number)
    if inv is None:
        raise CommandError("unknown_invoice", number)
    return inv


def live(w):
    """Every invoice that is not void, in number order."""
    for inv in w.invoices.values():
        if inv.status != "void":
            yield inv


def of_customer(w, cid):
    return [inv for inv in w.by_cust.get(cid, ()) if inv.status != "void"]


def has_period(w, cid, period):
    return any(inv.period == period for inv in of_customer(w, cid))


def oldest_first(invs):
    return sorted(invs, key=lambda inv: (inv.due, inv.number))


def cmd_show(w, cmd):
    inv = find(w, cmd.arg(0))
    cur = currencies.get(inv.currency)
    text = lambda amount: currencies.money_text(cur, amount)  # noqa: E731
    w.out.emit("invoice %s %s period=%d issued=%d due=%d status=%s"
               % (inv.number, inv.cust, inv.period, inv.issued, inv.due, state(inv)))
    for line in inv.lines:
        w.out.emit("  %s %s %s" % (line.kind, line.desc, text(line.amount)))
    for kind, amount in inv.discounts:
        w.out.emit("  discount %s %s" % (kind, text(-amount)))
    w.out.emit("  subtotal %s discount %s tax %s late %s total %s %s"
               % (text(inv.subtotal), text(inv.discount), text(inv.tax), text(inv.late),
                  text(inv.total), inv.currency))
    w.out.emit("  paid %s refunded %s outstanding %s"
               % (text(inv.paid), text(inv.refunded), text(inv.outstanding())))


def cmd_list(w, cmd):
    cmd.allow("state", "period")
    cid = cmd.arg(0, "")
    if cid:
        customers.get(w, cid)
    want_state = cmd.opt("state")
    if want_state not in (None, "open", "paid", "void"):
        raise CommandError("bad_value", want_state)
    want_period = cmd.opt("period")
    if want_period is not None:
        want_period = money.parse_int(want_period, 0, 100000)
    shown = 0
    for inv in w.invoices.values():
        if cid and inv.cust != cid:
            continue
        if want_state is not None and state(inv) != want_state:
            continue
        if want_period is not None and inv.period != want_period:
            continue
        cur = currencies.get(inv.currency)
        w.out.emit("%s %s p%d total=%s outstanding=%s %s" % (
            inv.number, inv.cust, inv.period, currencies.money_text(cur, inv.total),
            currencies.money_text(cur, inv.outstanding()), state(inv)))
        shown += 1
    w.out.emit("%d invoices" % shown)
