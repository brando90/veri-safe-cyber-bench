# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Bulk import (TSV blocks) and export (CSV or TSV documents).

An import block is all-or-nothing: rows are applied one after another inside
the command's savepoint and the first bad row refuses the whole block.  The
audit rows for an import are written in one batch at the end.
"""

import appointments
import audit
import billing
import customers
import formats
import money
import parse
import store
from errors import CommandError

IMPORT_USAGE = "import customers|services|appointments|payments"
EXPORT_USAGE = "export customers|services|appointments|invoices csv|tsv"


# ---------------------------------------------------------------- import

def build_customer(sess, rec):
    name = parse.text(rec["name"], "name")
    phone = parse.phone(rec["phone"])
    email = parse.email(rec.get("email", "-"))
    note = parse.text(rec.get("note", ""), "note", allow_empty=True, allow_tab=True)
    cid = customers.create(sess, name, phone, email, note)
    return "customer.add", parse.fmt_id("C", cid), customers.add_detail(name, phone, email, note)


def build_service(sess, rec):
    # Same validation, in the same order, as service-add.
    code = parse.code(rec["code"])
    minutes = parse.minutes(rec["minutes"])
    price = parse.amount(rec["price"])
    tax_bp = parse.rate(rec["tax"])
    name = parse.text(rec["name"], "name")
    if store.service(sess.conn, code) is not None:
        raise CommandError("duplicate-service: " + code)
    store.add_service(sess.conn, code, name, minutes, price, tax_bp)
    sess.expect.add("services")
    return "service.add", code, appointments.service_detail(name, minutes, price, tax_bp)


def build_appointment(sess, rec):
    # Same validation, in the same order, as book.
    cust = customers.lookup(sess, rec["customer"])
    svc = appointments.service(sess, parse.code(rec["service"]))
    day = parse.day(rec["day"])
    start = parse.time_of_day(rec["time"])
    appointments.check_slot(sess, cust, svc["minutes"], day, start)
    aid = store.add_appointment(sess.conn, cust["id"], svc["code"], day, start, svc["minutes"])
    sess.expect.add("appointments")
    return "appt.book", parse.fmt_id("A", aid), appointments.book_detail(
        cust["id"], svc["code"], day, start)


def build_payment(sess, rec):
    inv = parse.obj_id("I", rec["invoice"])
    cents = billing.positive_amount(rec["amount"])
    method = parse.method(rec["method"])
    pid, _ = billing.apply_payment(sess, inv, cents, method)
    return "payment.add", parse.fmt_id("P", pid), billing.payment_detail(inv, cents, method)


# KIND -> (permission to read it, permission to create it)
KIND_PERMS = {
    "customers": ("customer.view", "customer.write"),
    "services": ("appt.view", "service.write"),
    "appointments": ("appt.view", "appt.write"),
    "invoices": ("invoice.view", None),
    "payments": (None, "payment.record"),
}


class Kind:
    def __init__(self, columns, optional, build):
        self.columns = columns
        self.optional = optional
        self.build = build


KINDS = {
    "customers": Kind(("name", "phone", "email", "note"), ("email", "note"), build_customer),
    "services": Kind(("code", "name", "minutes", "price", "tax"), (), build_service),
    "appointments": Kind(("customer", "service", "day", "time"), (), build_appointment),
    "payments": Kind(("invoice", "amount", "method"), (), build_payment),
}


def check_header(kind, header):
    seen = set()
    for col in header:
        if col in seen:
            raise CommandError("import: duplicate column " + col)
        if col not in kind.columns:
            raise CommandError("import: unknown column " + col)
        seen.add(col)
    for col in kind.columns:
        if col not in seen and col not in kind.optional:
            raise CommandError("import: missing column " + col)


def cmd_import(sess, line, block):
    toks = parse.tokens(line)
    if len(toks) != 2 or toks[1] not in KINDS:
        raise parse.usage(IMPORT_USAGE)
    kind = KINDS[toks[1]]
    # Every row creates a record, so the import needs the permission of
    # that operation as well as import.run (README, "Operations").
    sess.require(KIND_PERMS[toks[1]][1])
    rows = [(n, text) for n, text in block if text != ""]
    if not rows:
        raise CommandError("import: missing header")
    header = rows[0][1].split("\t")
    check_header(kind, header)
    entries = []
    for n, text in rows[1:]:
        try:
            fields = formats.tsv_split(text)
        except ValueError:
            raise CommandError("import: line %d: bad escape" % n) from None
        if len(fields) != len(header):
            raise CommandError("import: line %d: expected %d fields, got %d"
                               % (n, len(header), len(fields)))
        try:
            action, obj, pairs = kind.build(sess, dict(zip(header, fields)))
        except CommandError as exc:
            raise CommandError("import: line %d: %s" % (n, exc)) from None
        entries.append((action, obj, formats.audit_detail(pairs)))
    audit.record_many(sess, entries)
    sess.emit("OK imported %d %s" % (len(entries), toks[1]))


# ---------------------------------------------------------------- export

def _customers(conn):
    return [[parse.fmt_id("C", r["id"]), r["name"], r["phone"], r["email"], r["note"],
             "archived" if r["archived"] else "active"] for r in store.all_customers(conn)]


def _services(conn):
    return [[r["code"], r["name"], r["minutes"], money.fmt(r["price_cents"]),
             money.fmt_rate(r["tax_bp"])] for r in store.all_services(conn)]


def _appointments(conn):
    return [[parse.fmt_id("A", r["id"]), parse.fmt_id("C", r["customer_id"]), r["service_code"],
             r["day"], parse.fmt_time(r["start"]), r["minutes"], r["status"],
             parse.fmt_id("I", r["invoice_id"]) if r["invoice_id"] else "-"]
            for r in store.all_appointments(conn)]


def _invoices(conn):
    return [[parse.fmt_id("I", r["id"]), parse.fmt_id("C", r["customer_id"]), r["status"],
             r["discount_pct"], money.fmt(r["net_cents"]), money.fmt(r["tax_cents"]),
             money.fmt(r["total_cents"]), money.fmt(r["paid_cents"])]
            for r in store.all_invoices(conn)]


EXPORTS = {
    "customers": (("id", "name", "phone", "email", "note", "status"), _customers),
    "services": (("code", "name", "minutes", "price", "tax"), _services),
    "appointments": (("id", "customer", "service", "day", "time", "minutes", "status",
                      "invoice"), _appointments),
    "invoices": (("id", "customer", "status", "discount", "net", "tax", "total", "paid"),
                 _invoices),
}


def cmd_export(sess, line):
    toks = parse.tokens(line)
    if len(toks) != 3 or toks[1] not in EXPORTS:
        raise parse.usage(EXPORT_USAGE)
    fmt = formats.check_fmt(toks[2], EXPORT_USAGE)
    header, rows_of = EXPORTS[toks[1]]
    sess.require(KIND_PERMS[toks[1]][0])
    formats.emit_table(sess, fmt, header, rows_of(sess.conn))
