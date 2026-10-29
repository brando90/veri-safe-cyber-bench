# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Invoice and payment commands."""

import money
import parse
import store
from errors import CommandError

def cmd_invoice_create(sess, line):
    toks = parse.tokens(line)
    cust = toks[1]
    discount = int(toks[2]) if len(toks) > 2 else 0
    # Check permission: invoice.write already in registry
    # Validate customer
    customer = store.customer_row(sess.conn, cust)
    if not customer:
        raise CommandError("unknown-customer: %s" % cust)
    if customer["status"] == "archived":
        raise CommandError("archived: %s" % cust)
    # Find appointments to invoice
    appts = store.appts_to_invoice(sess.conn, cust)
    if not appts:
        raise CommandError("nothing-to-invoice: %s" % cust)
    # Calculate totals
    lines = []
    total_net = 0
    total_tax = 0
    for appt in appts:
        service = store.service_row(sess.conn, appt["service"])
        price_cents = money.cents(service["price"])
        tax_pct = service["tax"]
        discount_cents = price_cents * discount // 100
        net = price_cents - discount_cents
        tax = money.round_per_line(net, tax_pct)[1]
        total_net += net
        total_tax += tax
        lines.append((appt["id"], service["code"], net, tax))
    total = total_net + total_tax
    # Create invoice
    invoice_id = store.invoice_add(sess.conn, cust, discount, total_net, total_tax, total)
    sess.out.write("OK invoice %s total %s\n" % (invoice_id, money.format(total)))
    # Audit: invoice.create
    detail = {"customer": cust, "lines": len(lines), "total": money.format(total)}
    sess.audit("invoice.create", invoice_id, detail)
    for line in lines:
        sess.audit("invoice.line", invoice_id, {"appointment": line[0], "service": line[1], "net": money.format(line[2]), "tax": money.format(line[3])})