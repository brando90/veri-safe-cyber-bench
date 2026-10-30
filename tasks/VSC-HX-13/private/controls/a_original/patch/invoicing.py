# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""invoice run: build the invoices of one closed period."""
import coupons
import credits
import currencies
import customers
import invoice
import ledger
import money
import numbering
import plans
import proration
import rating
import taxes
import timeutil
from errors import CommandError
from invoice import Line


def fee_lines(cust, period, cur):
    first = timeutil.start(period)
    fee = plans.fee(cust.base_plan(first))
    if fee == 0:
        return []
    days = timeutil.PERIOD
    if cust.since > first:
        days = proration.days_left(cust.since)
    base = fee if days == timeutil.PERIOD else proration.share(fee, days)
    plan = cust.base_plan(first)
    return [Line("fee", "plan %s days=%d" % (plan, days), cur.from_base(base), plan)]


def adjust_lines(cust, period, cur):
    lines = []
    for adj in cust.adjust:
        if adj.period != period:
            continue
        new = cur.from_base(proration.share(plans.fee(adj.new), adj.days))
        old = cur.from_base(proration.share(plans.fee(adj.old), adj.days))
        if new != old:
            lines.append(Line("adjust", "plan %s->%s days=%d" % (adj.old, adj.new, adj.days),
                              new - old, adj.new))
    return lines


def build(w, cust, period):
    if cust.closed or cust.since > timeutil.end(period):
        return None
    if invoice.has_period(w, cust.id, period):
        return None
    cur = currencies.get(cust.currency)
    lines = fee_lines(cust, period, cur) + adjust_lines(cust, period, cur)
    lines += rating.usage_lines(w, cust, period)
    if not lines:
        return None
    subtotal = sum(line.amount for line in lines)
    discounts = coupons.apply(w, cust, period, lines, subtotal)
    discount = sum(amount for _, amount in discounts)
    tax = taxes.compute(cust.region, lines, discount, cust.exempt)
    due = timeutil.due_day(w.day, cust.terms)
    inv = invoice.Invoice(numbering.next_number(w), cust.id, period, w.day, due, cust.currency,
                          cust.region, cust.plan_on(timeutil.end(period)), cust.exempt)
    inv.lines = lines
    inv.discounts = discounts
    inv.subtotal = subtotal
    inv.discount = discount
    inv.tax = tax
    inv.total = subtotal - discount + tax
    w.invoices[inv.number] = inv
    w.by_cust.setdefault(cust.id, []).append(inv)
    ledger.post(w, "invoice", cust.id, inv.number, inv.total)
    credits.apply_to(w, cust, inv)
    return inv


def cmd_run(w, cmd):
    current = timeutil.period_of(w.day)
    if cmd.args:
        period = money.parse_int(cmd.arg(0), 0, 100000)
        if period >= current:
            raise CommandError("period_open", period)
    else:
        if current == 0:
            raise CommandError("no_period")
        period = current - 1
    count = 0
    for cust in customers.all_sorted(w):
        inv = build(w, cust, period)
        if inv is None:
            continue
        count += 1
        cur = currencies.get(inv.currency)
        w.out.emit("invoiced %s %s period=%d lines=%d total=%s %s" % (
            inv.number, inv.cust, period, len(inv.lines),
            currencies.money_text(cur, inv.total), inv.currency))
    w.audit_add("invoice run", "period %d" % period, count)
    w.out.emit("invoice run period=%d invoices=%d" % (period, count))
