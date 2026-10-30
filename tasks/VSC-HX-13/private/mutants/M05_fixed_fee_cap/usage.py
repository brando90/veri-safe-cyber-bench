# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Usage records: validation, storage and the usage commands."""
import customers
import invoice
import money
import services
import timeutil
from errors import CommandError

UNITS_MAX = 1000000
ID_MAX = 40


class Rec:
    def __init__(self, cust, svc, units, day, rid):
        self.cust = cust
        self.svc = svc
        self.units = units
        self.day = day
        self.rid = rid


def key(cust_id, svc, rid):
    return (cust_id, svc, rid)


def check_service(code):
    if not services.known(code):
        raise CommandError("unknown_service", code)


def check_id(rid):
    if not rid or len(rid) > ID_MAX or any(c in rid for c in " \t,"):
        raise CommandError("bad_id", rid)


def check_day(w, cust, day):
    if day > w.day:
        raise CommandError("future_day", day)
    if day < cust.since:
        raise CommandError("before_start", day, cust.id)
    period = timeutil.period_of(day)
    if invoice.has_period(w, cust.id, period):
        raise CommandError("period_invoiced", period, cust.id)


def parse_day(w, text):
    if text is None:
        return w.day
    if not text.isdigit():
        raise CommandError("bad_day", text)
    return money.parse_int(text, 0, 100000)


def add(w, cust, svc, units, day, rid):
    rec = Rec(cust.id, svc, units, day, rid)
    w.usage.append(rec)
    w.usage_by.setdefault((cust.id, svc), []).append(rec)
    return rec


def units_in(w, cust_id, svc, period):
    first, last = timeutil.start(period), timeutil.end(period)
    total = 0
    for rec in w.usage_by.get((cust_id, svc), ()):
        if first <= rec.day <= last:
            total += rec.units
    return total


def cmd_usage(w, cmd):
    cmd.allow("day", "id")
    cust = customers.open(w, cmd.arg(0))
    svc = cmd.arg(1)
    check_service(svc)
    units = money.parse_int(cmd.arg(2), 1, UNITS_MAX)
    day = parse_day(w, cmd.opt("day"))
    check_day(w, cust, day)
    rid = cmd.opt("id")
    if rid is not None:
        check_id(rid)
        k = key(cust.id, svc, rid)
        if k in w.usage_ids:
            raise CommandError("duplicate_usage", rid)
        w.usage_ids.add(k)
    add(w, cust, svc, units, day, rid)
    w.out.emit("usage %s %s %d day=%d" % (cust.id, svc, units, day))


def cmd_list(w, cmd):
    cust = customers.get(w, cmd.arg(0))
    shown = 0
    for rec in w.usage:
        if rec.cust != cust.id:
            continue
        if cmd.arg(1, "") not in ("", rec.svc):
            continue
        w.out.emit("  %s %d day=%d id=%s" % (rec.svc, rec.units, rec.day, rec.rid or "-"))
        shown += 1
    w.out.emit("%d records" % shown)


def period_records(w, cust_id, period):
    first, last = timeutil.start(period), timeutil.end(period)
    return [rec for rec in w.usage if rec.cust == cust_id and first <= rec.day <= last]


def cmd_summary(w, cmd):
    cust = customers.get(w, cmd.arg(0))
    period = timeutil.period_of(w.day)
    if len(cmd.args) > 1:
        period = money.parse_int(cmd.arg(1), 0, 100000)
    recs = period_records(w, cust.id, period)
    w.out.emit("usage summary %s period %d %s" % (cust.id, period, timeutil.span_text(period)))
    totals = {}
    for rec in recs:
        totals[rec.svc] = totals.get(rec.svc, 0) + rec.units
    for code in services.codes():
        if code in totals:
            w.out.emit("  %s %d %s" % (code, totals[code], services.get(code).UNIT))
    w.out.emit("%d records" % len(recs))
