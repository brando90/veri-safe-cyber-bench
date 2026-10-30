# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The program's own consistency check, run after every command.

A violation is reported as INVARIANT: on standard error and ends the run
with exit status 86.
"""
from errors import InvariantViolation


def fail(msg, *params):
    raise InvariantViolation(msg % params)


def check_invoice(inv):
    subtotal = sum(line.amount for line in inv.lines if line.kind != "late")
    late = sum(line.amount for line in inv.lines if line.kind == "late")
    if subtotal != inv.subtotal:
        fail("%s: lines add up to %d but subtotal is %d", inv.number, subtotal, inv.subtotal)
    if late != inv.late:
        fail("%s: late lines add up to %d but late is %d", inv.number, late, inv.late)
    if inv.total != inv.subtotal - inv.discount + inv.tax + inv.late:
        fail("%s: total %d does not match its parts", inv.number, inv.total)
    if inv.total < 0 or inv.discount < 0 or inv.tax < 0:
        fail("%s: negative amount", inv.number)
    if inv.discount != sum(amount for _, amount in inv.discounts):
        fail("%s: discount lines do not add up", inv.number)
    for line in inv.lines:
        if line.amount < 0 and line.kind != "adjust":
            fail("%s: negative %s line", inv.number, line.kind)
    if inv.exempt and inv.tax != 0:
        fail("%s: tax charged to an exempt customer", inv.number)
    if inv.paid < 0 or not 0 <= inv.refunded <= inv.paid:
        fail("%s: refunded %d exceeds paid %d", inv.number, inv.refunded, inv.paid)
    if inv.paid - inv.refunded > inv.total:
        fail("%s: net payments %d exceed the total %d", inv.number, inv.paid - inv.refunded, inv.total)
    if inv.late_day is not None and inv.late_day <= inv.due:
        fail("%s: late fee added on day %d, due day is %d", inv.number, inv.late_day, inv.due)
    if (inv.late_day is None) != (inv.late == 0):
        fail("%s: late fee and its day disagree", inv.number)


def check_usage(w):
    for rec in w.usage:
        if rec.units <= 0 or rec.day > w.day:
            fail("usage record of %s for %s is out of range", rec.cust, rec.svc)
        if rec.cust not in w.customers:
            fail("usage record for unknown customer %s", rec.cust)


def check_numbers(w):
    expected = 0
    for number in w.invoices:
        expected += 1
        if number != "INV-%04d" % expected:
            fail("invoice %s is out of sequence", number)
        if w.invoices[number].cust not in w.customers:
            fail("%s belongs to an unknown customer", number)


def full_check(w):
    check_usage(w)
    check_numbers(w)
    for inv in w.invoices.values():
        check_invoice(inv)
    if w.seq != len(w.invoices):
        fail("invoice numbers: %d issued, %d held", w.seq, len(w.invoices))
    for cust in w.customers.values():
        if cust.credit < 0:
            fail("%s: negative credit", cust.id)
        if cust.credit != w.credit_sum.get(cust.id, 0):
            fail("%s: credit %d differs from ledger %d", cust.id, cust.credit,
                 w.credit_sum.get(cust.id, 0))
        for cp in cust.coupons:
            if cp.used < 0:
                fail("%s: coupon use count", cust.id)
