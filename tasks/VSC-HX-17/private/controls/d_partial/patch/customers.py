# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Customer accounts: lookup, creation, listing and closing."""
import re

import output
import regions
import tiers
from errors import CommandError
from model import Customer

ID_RE = re.compile(r"c-[a-z0-9]{1,12}")
LIVE_STATES = ("open", "partial", "backorder")


def get(w, cid):
    cust = w.customers.get(cid)
    if cust is None:
        raise CommandError("unknown_customer", cid)
    return cust


def open(w, cid):
    cust = get(w, cid)
    if cust.status == "closed":
        raise CommandError("closed", cid)
    return cust


def all_sorted(w):
    return [w.customers[k] for k in sorted(w.customers)]


def open_orders(w, cid):
    """Orders of CID that still have something pending."""
    return [o for o in w.orders.values() if o.cust == cid and o.status in LIVE_STATES]


def cmd_add(w, cmd):
    cmd.allow("tier", "name")
    cid = cmd.arg(0)
    if not ID_RE.fullmatch(cid):
        raise CommandError("bad_id", cid)
    if cid in w.customers:
        raise CommandError("customer_exists", cid)
    region = cmd.arg(1)
    if not regions.known(region):
        raise CommandError("unknown_region", region)
    tier = tiers.check(cmd.opt("tier", "basic"))
    name = cmd.opt("name", cid)
    if not name.strip() or len(name) > 60:
        raise CommandError("bad_value", name)
    w.customers[cid] = Customer(cid, name, region, tier, created=w.day)
    w.audit_add("customer add", cid, region, tier)
    w.out.emit("customer %s added region=%s tier=%s" % (cid, region, tier))


def describe(cust):
    return [
        "customer %s" % cust.id,
        "  name=%s region=%s tier=%s carrier=%s split=%s hold=%s" % (
            output.quote(cust.name), cust.region, cust.tier, cust.carrier,
            "yes" if cust.split else "no", "yes" if cust.hold else "no"),
        "  po=%s email=%s note=%s" % (output.dash(cust.po), output.dash(cust.email),
                                     output.dash(cust.note)),
        "  status=%s since day %d" % (cust.status, cust.created),
    ]


def cmd_show(w, cmd):
    for line in describe(get(w, cmd.arg(0))):
        w.out.emit(line)


def cmd_list(w, cmd):
    cmd.allow("tier", "region", "status")
    rows = []
    for cust in all_sorted(w):
        if cmd.opt("tier") and cust.tier != cmd.opt("tier"):
            continue
        if cmd.opt("region") and cust.region != cmd.opt("region"):
            continue
        if cmd.opt("status") and cust.status != cmd.opt("status"):
            continue
        rows.append("%s %s %s %s" % (cust.id, cust.region, cust.tier, cust.status))
    for row in rows:
        w.out.emit(row)
    w.out.emit("%d customers" % len(rows))


def cmd_history(w, cmd):
    cid = cmd.arg(0)
    get(w, cid)
    count = 0
    for seq, day, action, subject, details in w.audit:
        if subject == cid:
            w.out.emit("  #%d day %d %s %s" % (seq, day, action, " ".join(details)))
            count += 1
    if not count:
        w.out.emit("  (none)")


def cmd_close(w, cmd):
    cust = get(w, cmd.arg(0))
    if cust.status == "closed":
        raise CommandError("already_closed", cust.id)
    cust.status = "closed"
    w.audit_add("customer close", cust.id)
    w.out.emit("customer %s closed" % cust.id)
