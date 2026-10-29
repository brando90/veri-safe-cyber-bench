# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Invoices and payments."""

import audit
import customers
import money
import parse
import store
from errors import CommandError


def lookup(sess, text):
    inv = parse.obj_id("I", text)
    return get(sess, inv)


def get(sess, inv):
    row = store.invoice(sess.conn, inv)
    if row is None:
        raise CommandError("unknown-invoice: " + parse.fmt_id("I", inv))
    return row


def positive_amount(text):
    cents = parse.amount(text)
    if cents == 0:
        raise CommandError("bad-money: " + text)
    return cents


def cmd_invoice_create(sess, line):
    usage_text = "invoice-create CUST [DISCOUNT]"
    toks, rest = parse.take(line, 2)
    if rest is None or len(parse.tokens(rest)) > 1:
        raise parse.usage(usage_text)
    cust = customers.lookup(sess, toks[1])
    discount_pct = parse.percent(rest) if rest else 0
    appts = store.uninvoiced_done(sess.conn, cust["id"])
    ident = parse.fmt_id("C", cust["id"])
    if not appts:
        raise CommandError("nothing-to-invoice: " + ident)
    lines = []
    for a in appts:
        discount, net, tax, total = money.line_amounts(a["price_cents"], discount_pct,
                                                       a["tax_bp"])
        lines.append((a, discount, net, tax, total))
    net_sum = sum(l[2] for l in lines)
    tax_sum = sum(l[3] for l in lines)
    total_sum = sum(l[4] for l in lines)
    inv = store.add_invoice(sess.conn, cust["id"], discount_pct, net_sum, tax_sum, total_sum)
    for pos, (a, discount, net, tax, total) in enumerate(lines, 1):
        store.add_line(sess.conn, inv, pos, a["id"], a["service_code"], a["price_cents"],
                       discount, net, a["tax_bp"], tax, total)
    sess.expect.add("invoices")
    sess.expect.add("invoice_lines", len(lines))
    audit.record(sess, "invoice.create", parse.fmt_id("I", inv),
                 [("customer", ident), ("lines", len(lines)), ("total", money.fmt(total_sum))])
    sess.emit("OK invoice %s total %s" % (parse.fmt_id("I", inv), money.fmt(total_sum)))


def cmd_invoice_show(sess, line):
    toks, rest = parse.take(line, 2)
    if rest is None or rest != "":
        raise parse.usage("invoice-show INV")
    row = lookup(sess, toks[1])
    sess.emit("invoice %s customer %s status %s discount %d%%" % (
        parse.fmt_id("I", row["id"]), parse.fmt_id("C", row["customer_id"]), row["status"],
        row["discount_pct"]))
    for l in store.invoice_lines(sess.conn, row["id"]):
        sess.emit("line %d %s %s price=%s discount=%s net=%s tax=%s total=%s" % (
            l["pos"], parse.fmt_id("A", l["appt_id"]), l["service_code"],
            money.fmt(l["price_cents"]), money.fmt(l["discount_cents"]),
            money.fmt(l["net_cents"]), money.fmt(l["tax_cents"]), money.fmt(l["total_cents"])))
    sess.emit("net=%s tax=%s total=%s paid=%s balance=%s" % (
        money.fmt(row["net_cents"]), money.fmt(row["tax_cents"]), money.fmt(row["total_cents"]),
        money.fmt(row["paid_cents"]), money.fmt(row["total_cents"] - row["paid_cents"])))


def apply_payment(sess, inv, cents, method):
    """Record a validated payment; returns (payment id, remaining balance)."""
    row = get(sess, inv)
    ident = parse.fmt_id("I", inv)
    if row["status"] == "void":
        raise CommandError("invoice-void: " + ident)
    if row["status"] == "paid":
        raise CommandError("invoice-paid: " + ident)
    balance = row["total_cents"] - row["paid_cents"]
    if cents > balance:
        raise CommandError("overpayment: %s balance %s" % (ident, money.fmt(balance)))
    pid = store.add_payment(sess.conn, inv, cents, method)
    sess.expect.add("payments")
    if cents == balance:
        store.set_invoice_status(sess.conn, inv, "paid")
    return pid, balance - cents


def payment_detail(inv, cents, method):
    return [("invoice", parse.fmt_id("I", inv)), ("amount", money.fmt(cents)),
            ("method", method)]


def cmd_pay(sess, line):
    toks, rest = parse.take(line, 4)
    if rest is None or rest != "":
        raise parse.usage("pay INV AMOUNT METHOD")
    inv = parse.obj_id("I", toks[1])
    cents = positive_amount(toks[2])
    method = parse.method(toks[3])
    pid, balance = apply_payment(sess, inv, cents, method)
    audit.record(sess, "payment.add", parse.fmt_id("P", pid), payment_detail(inv, cents, method))
    sess.emit("OK payment %s balance %s" % (parse.fmt_id("P", pid), money.fmt(balance)))


def cmd_invoice_void(sess, line):
    toks, rest = parse.take(line, 2)
    if rest is None or rest == "":
        raise parse.usage("invoice-void INV REASON")
    row = lookup(sess, toks[1])
    ident = parse.fmt_id("I", row["id"])
    reason = parse.text(rest, "reason", allow_tab=True)
    if row["status"] == "void":
        raise CommandError("invoice-void: " + ident)
    if row["paid_cents"] > 0:
        raise CommandError("invoice-paid: " + ident)
    store.set_invoice_status(sess.conn, row["id"], "void")
    audit.record(sess, "invoice.void", ident, [("reason", reason)])
    sess.emit("OK void " + ident)
