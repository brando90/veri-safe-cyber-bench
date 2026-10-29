# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Customer records."""

import appointments
import audit
import parse
import store
from errors import CommandError


def lookup(sess, text):
    """Customer row for an id written as C<digits>, or CommandError."""
    cid = parse.obj_id("C", text)
    return get(sess, cid)


def get(sess, cid):
    row = store.customer(sess.conn, cid)
    if row is None:
        raise CommandError("unknown-customer: " + parse.fmt_id("C", cid))
    return row


def create(sess, name, phone, email, note):
    """Insert a validated customer; returns the new id."""
    cid = store.add_customer(sess.conn, name, phone, email, note)
    sess.expect.add("customers")
    return cid


def add_detail(name, phone, email, note):
    return [("name", name), ("phone", phone), ("email", email), ("note", note)]


def cmd_add(sess, line):
    toks, rest = parse.take(line, 3)
    if rest is None or rest == "":
        raise parse.usage("customer-add PHONE EMAIL NAME")
    phone = parse.phone(toks[1])
    email = parse.email(toks[2])
    name = parse.text(rest, "name")
    cid = create(sess, name, phone, email, "")
    audit.record(sess, "customer.add", parse.fmt_id("C", cid), add_detail(name, phone, email, ""))
    sess.emit("OK customer " + parse.fmt_id("C", cid))


def cmd_note(sess, line):
    toks, rest = parse.take(line, 2)
    if rest is None:
        raise parse.usage("customer-note CUST [TEXT]")
    row = lookup(sess, toks[1])
    note = parse.text(rest, "note", allow_empty=True, allow_tab=True)
    if row["archived"]:
        raise CommandError("archived: " + parse.fmt_id("C", row["id"]))
    store.set_note(sess.conn, row["id"], note)
    audit.record(sess, "customer.note", parse.fmt_id("C", row["id"]), [("note", note)])
    sess.emit("OK customer %s note" % parse.fmt_id("C", row["id"]))


def cmd_show(sess, line):
    toks, rest = parse.take(line, 2)
    if rest is None or rest != "":
        raise parse.usage("customer-show CUST")
    row = lookup(sess, toks[1])
    sess.emit("customer " + parse.fmt_id("C", row["id"]))
    sess.emit("name: " + row["name"])
    sess.emit("phone: " + row["phone"])
    sess.emit("email: " + row["email"])
    sess.emit("note: " + row["note"])
    sess.emit("status: " + ("archived" if row["archived"] else "active"))


def cmd_find(sess, line):
    toks, rest = parse.take(line, 1)
    if not rest:
        raise parse.usage("customer-find TEXT")
    rows = store.find_customers(sess.conn, rest)
    for row in rows:
        mark = " [archived]" if row["archived"] else ""
        sess.emit("%s %s%s" % (parse.fmt_id("C", row["id"]), row["name"], mark))
    sess.emit("matches: %d" % len(rows))


def cmd_archive(sess, line):
    toks, rest = parse.take(line, 2)
    if rest is None or rest != "":
        raise parse.usage("customer-archive CUST")
    row = lookup(sess, toks[1])
    ident = parse.fmt_id("C", row["id"])
    if row["archived"]:
        raise CommandError("archived: " + ident)
    booked = store.booked_for(sess.conn, row["id"])
    if booked:
        sess.require("appt.cancel")
    for appt in booked:
        appointments.change_status(sess, appt, "cancelled")
    store.set_archived(sess.conn, row["id"])
    audit.record(sess, "customer.archive", ident, [("cancelled", len(booked))])
    sess.emit("OK archived %s cancelled %d" % (ident, len(booked)))
