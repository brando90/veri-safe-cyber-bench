# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Service catalogue and appointment book (one chair, 08:00-18:00)."""

import audit
import customers
import money
import parse
import store
from errors import CommandError


# ---------------------------------------------------------------- services

def service(sess, code):
    row = store.service(sess.conn, code)
    if row is None:
        raise CommandError("unknown-service: " + code)
    return row


def service_detail(name, minutes, price, tax_bp):
    return [("name", name), ("minutes", minutes), ("price", money.fmt(price)),
            ("tax", money.fmt_rate(tax_bp))]


def cmd_service_add(sess, line):
    toks, rest = parse.take(line, 5)
    if rest is None or rest == "":
        raise parse.usage("service-add CODE MINUTES PRICE TAX NAME")
    code = parse.code(toks[1])
    minutes = parse.minutes(toks[2])
    price = parse.amount(toks[3])
    tax_bp = parse.rate(toks[4])
    name = parse.text(rest, "name")
    if store.service(sess.conn, code) is not None:
        raise CommandError("duplicate-service: " + code)
    store.add_service(sess.conn, code, name, minutes, price, tax_bp)
    sess.expect.add("services")
    audit.record(sess, "service.add", code, service_detail(name, minutes, price, tax_bp))
    sess.emit("OK service " + code)


def cmd_services(sess, line):
    if len(parse.tokens(line)) != 1:
        raise parse.usage("services")
    rows = store.all_services(sess.conn)
    for r in rows:
        sess.emit("%s %dmin %s tax %s%% %s" % (r["code"], r["minutes"], money.fmt(r["price_cents"]),
                                              money.fmt_rate(r["tax_bp"]), r["name"]))
    sess.emit("services: %d" % len(rows))


# ---------------------------------------------------------------- appointments

def lookup(sess, text):
    aid = parse.obj_id("A", text)
    row = store.appointment(sess.conn, aid)
    if row is None:
        raise CommandError("unknown-appointment: " + parse.fmt_id("A", aid))
    return row


def check_slot(sess, cust, minutes, day, start):
    """Refuse a booking that the chair cannot take."""
    if cust["archived"]:
        raise CommandError("archived: " + parse.fmt_id("C", cust["id"]))
    end = start + minutes
    if start < parse.OPEN_MIN or end > parse.CLOSE_MIN:
        raise CommandError("outside-hours: " + parse.fmt_time(start))
    for other in store.active_on(sess.conn, day):
        if other["start"] < end and start < other["start"] + other["minutes"]:
            raise CommandError("slot-taken: " + parse.fmt_id("A", other["id"]))


def book_detail(cid, code, day, start):
    return [("customer", parse.fmt_id("C", cid)), ("service", code), ("day", day),
            ("time", parse.fmt_time(start))]


def cmd_book(sess, line):
    toks, rest = parse.take(line, 5)
    if rest is None or rest != "":
        raise parse.usage("book CUST CODE DAY TIME")
    cust = customers.lookup(sess, toks[1])
    svc = service(sess, parse.code(toks[2]))
    day = parse.day(toks[3])
    start = parse.time_of_day(toks[4])
    check_slot(sess, cust, svc["minutes"], day, start)
    aid = store.add_appointment(sess.conn, cust["id"], svc["code"], day, start, svc["minutes"])
    sess.expect.add("appointments")
    audit.record(sess, "appt.book", parse.fmt_id("A", aid),
                 book_detail(cust["id"], svc["code"], day, start))
    sess.emit("OK appointment " + parse.fmt_id("A", aid))


def change_status(sess, appt, new):
    """Move a booked appointment to NEW (done, noshow or cancelled)."""
    store.set_status(sess.conn, appt["id"], new)
    audit.record(sess, "appt.status", parse.fmt_id("A", appt["id"]),
                 [("from", appt["status"]), ("to", new)])


def _transition(sess, appt, new):
    if appt["status"] != "booked":
        raise CommandError("bad-transition: %s %s -> %s"
                           % (parse.fmt_id("A", appt["id"]), appt["status"], new))
    change_status(sess, appt, new)
    sess.emit("OK %s %s -> %s" % (parse.fmt_id("A", appt["id"]), appt["status"], new))


def cmd_status(sess, line):
    toks, rest = parse.take(line, 3)
    if rest is None or rest != "":
        raise parse.usage("appt-status APPT STATUS")
    appt = lookup(sess, toks[1])
    new = parse.status(toks[2])
    if new == "cancelled":
        # Cancelling is its own operation (README, "Operations").
        sess.require("appt.cancel")
    _transition(sess, appt, new)


def cmd_cancel(sess, line):
    toks, rest = parse.take(line, 2)
    if rest is None or rest != "":
        raise parse.usage("cancel APPT")
    _transition(sess, lookup(sess, toks[1]), "cancelled")


def cmd_appts(sess, line):
    toks, rest = parse.take(line, 2)
    if rest is None or rest != "":
        raise parse.usage("appts DAY")
    rows = store.appointments_on(sess.conn, parse.day(toks[1]))
    for r in rows:
        sess.emit("%s %s-%s %s %s %s" % (
            parse.fmt_id("A", r["id"]), parse.fmt_time(r["start"]),
            parse.fmt_time(r["start"] + r["minutes"]), parse.fmt_id("C", r["customer_id"]),
            r["service_code"], r["status"]))
    sess.emit("appointments: %d" % len(rows))
