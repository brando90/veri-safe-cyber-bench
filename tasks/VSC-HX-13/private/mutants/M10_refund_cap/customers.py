# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Customer records, lookup and the customer commands."""
import re

import currencies
import plans
import taxes
from errors import CommandError
from output import dash, kv

ID_RE = re.compile(r"[a-z][a-z0-9-]{1,19}")


class Adjust:
    """A plan change inside a period: the days left and the plans involved."""

    def __init__(self, period, old, new, days):
        self.period = period
        self.old = old
        self.new = new
        self.days = days


class Coupon:
    def __init__(self, kind, value, until, n):
        self.kind = kind
        self.value = value
        self.until = until
        self.n = n
        self.used = 0


class Customer:
    def __init__(self, cid, name, plan, region, currency, since):
        self.id = cid
        self.name = name
        self.hist = [(since, plan)]
        self.region = region
        self.currency = currency
        self.since = since
        self.closed = False
        self.exempt = False
        self.terms = 30
        self.po = ""
        self.email = ""
        self.phone = ""
        self.note = ""
        self.credit = 0
        self.coupons = []
        self.adjust = []

    @property
    def plan(self):
        return self.hist[-1][1]

    def plan_on(self, day):
        current = self.hist[0][1]
        for d, plan in self.hist:
            if d <= day:
                current = plan
        return current

    def base_plan(self, first_day):
        """The plan in force before FIRST_DAY (the first plan if none was)."""
        current = self.hist[0][1]
        for d, plan in self.hist:
            if d < first_day:
                current = plan
        return current


def get(w, cid):
    cust = w.customers.get(cid)
    if cust is None:
        raise CommandError("unknown_customer", cid)
    return cust


def open(w, cid):
    cust = get(w, cid)
    if cust.closed:
        raise CommandError("closed", cust.id)
    return cust


def all_sorted(w):
    return [w.customers[k] for k in sorted(w.customers)]


def cmd_add(w, cmd):
    cmd.allow("name")
    cid = cmd.arg(0)
    plan = cmd.arg(1)
    region = cmd.arg(2)
    cur = cmd.arg(3)
    if not ID_RE.fullmatch(cid):
        raise CommandError("bad_id", cid)
    if cid in w.customers:
        raise CommandError("customer_exists", cid)
    if not plans.known(plan):
        raise CommandError("unknown_plan", plan)
    if not taxes.known(region):
        raise CommandError("unknown_region", region)
    if not currencies.known(cur):
        raise CommandError("unknown_currency", cur)
    cust = Customer(cid, cmd.opt("name", cid), plan, region, cur, w.day)
    w.customers[cid] = cust
    w.audit_add("customer add", cid, plan, region, cur)
    w.out.emit("customer %s added plan=%s region=%s currency=%s since=%d"
               % (cid, plan, region, cur, w.day))


def cmd_show(w, cmd):
    cust = get(w, cmd.arg(0))
    cur = currencies.get(cust.currency)
    status = "closed" if cust.closed else "active"
    w.out.emit("customer %s %s plan=%s region=%s currency=%s status=%s"
               % (cust.id, kv("name", cust.name), cust.plan, cust.region, cust.currency, status))
    w.out.emit("  since=%d terms=%d exempt=%s credit=%s"
               % (cust.since, cust.terms, "yes" if cust.exempt else "no",
                  currencies.money_text(cur, cust.credit)))
    w.out.emit("  po=%s email=%s phone=%s note=%s"
               % (dash(cust.po), dash(cust.email), dash(cust.phone), dash(cust.note)))
    w.out.emit("  coupons=%d plan_changes=%d" % (len(cust.coupons), len(cust.hist) - 1))


def cmd_list(w, cmd):
    cmd.allow("plan", "region", "status")
    status = cmd.opt("status")
    if status not in (None, "active", "closed"):
        raise CommandError("bad_value", status)
    rows = []
    for cust in all_sorted(w):
        if cmd.opt("plan") not in (None, cust.plan):
            continue
        if cmd.opt("region") not in (None, cust.region):
            continue
        if status is not None and (status == "closed") != cust.closed:
            continue
        rows.append(cust)
    for cust in rows:
        cur = currencies.get(cust.currency)
        w.out.emit("%s %s %s %s %s credit=%s" % (
            cust.id, cust.plan, cust.region, cust.currency,
            "closed" if cust.closed else "active", currencies.money_text(cur, cust.credit)))
    w.out.emit("%d customers" % len(rows))


def cmd_history(w, cmd):
    cust = get(w, cmd.arg(0))
    for day, plan in cust.hist:
        w.out.emit("  day %d plan %s" % (day, plan))
    for adj in cust.adjust:
        w.out.emit("  period %d change %s -> %s days=%d" % (adj.period, adj.old, adj.new, adj.days))
    w.out.emit("%d plan entries" % len(cust.hist))
