# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Coupons: the coupon commands and the discounts applied to one invoice."""
import currencies
import customers
import discounts
import money
import timeutil
from customers import Coupon
from errors import CommandError


class Ctx:
    """What a discount kind may look at: the sums of one invoice."""

    def __init__(self, period, lines, subtotal, exp):
        self.period = period
        self.subtotal = subtotal
        self.exp = exp
        self.fee = sum(line.amount for line in lines if line.kind == "fee")
        self.usage = sum(line.amount for line in lines if line.kind == "usage")
        self.adjust = sum(line.amount for line in lines if line.kind == "adjust")


def apply(w, cust, period, lines, subtotal):
    """Discounts for the invoice being built: [(kind, amount)], uses counted."""
    cur = currencies.get(cust.currency)
    ctx = Ctx(period, lines, subtotal, cur.EXP)
    given = []
    total = 0
    for cp in cust.coupons:
        if cp.until is not None and timeutil.start(period) > cp.until:
            continue
        amount = discounts.get(cp.kind).amount(ctx, cp)
        amount = min(amount, subtotal - total)
        if amount <= 0:
            continue
        cp.used += 1
        total += amount
        given.append((cp.kind, amount))
    return given


def cmd_add(w, cmd):
    cmd.allow("until", "n")
    cust = customers.open(w, cmd.arg(0))
    kind = cmd.arg(1)
    if not discounts.known(kind):
        raise CommandError("unknown_kind", kind)
    mod = discounts.get(kind)
    cur = currencies.get(cust.currency)
    value = mod.validate(cmd.arg(2), cur.EXP)
    until = cmd.opt("until")
    if until is not None:
        until = money.parse_int(until, 0, 100000)
    n = money.parse_int(cmd.opt("n", str(mod.DEFAULT_N)), 0, 120)
    cust.coupons.append(Coupon(kind, value, until, n))
    w.audit_add("coupon add", cust.id, kind, value)
    w.out.emit("coupon %s #%d %s" % (cust.id, len(cust.coupons), kind))


def cmd_rm(w, cmd):
    cust = customers.open(w, cmd.arg(0))
    idx = money.parse_int(cmd.arg(1), 1, 1000)
    if idx > len(cust.coupons):
        raise CommandError("unknown_coupon", cust.id, idx)
    gone = cust.coupons.pop(idx - 1)
    w.audit_add("coupon rm", cust.id, gone.kind)
    w.out.emit("coupon %s removed %s" % (cust.id, gone.kind))


def cmd_list(w, cmd):
    cust = customers.get(w, cmd.arg(0))
    for i, cp in enumerate(cust.coupons, 1):
        until = "-" if cp.until is None else str(cp.until)
        w.out.emit("  #%d %s value=%d until=%s n=%d used=%d" % (i, cp.kind, cp.value, until, cp.n, cp.used))
    w.out.emit("%d coupons" % len(cust.coupons))


def cmd_kinds(w, cmd):
    for kind in discounts.kinds():
        mod = discounts.get(kind)
        w.out.emit("%s target=%s percentage=%s default_n=%d" % (
            kind, mod.targets(), "yes" if mod.is_percentage() else "no", mod.DEFAULT_N))
    w.out.emit("%d kinds" % len(discounts.kinds()))
