# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""service, region and currency listings."""
import currencies
import customers
import money
import plans
import services
import taxes
from errors import CommandError
from plans import ORDER


def cmd_service_list(w, cmd):
    for code in services.codes():
        svc = services.get(code)
        w.out.emit("%s block=%d unit=%s mode=%s min=%d tiers=%d" % (
            code, svc.BLOCK, svc.UNIT, svc.MODE, svc.MIN_CHARGE, len(svc.TIERS)))
    w.out.emit("%d services" % len(services.codes()))


def cmd_service_show(w, cmd):
    code = cmd.arg(0)
    if not services.known(code):
        raise CommandError("unknown_service", code)
    svc = services.get(code)
    w.out.emit("service %s %s" % (code, svc.LABEL))
    w.out.emit("  unit=%s block=%d mode=%s min=%d" % (svc.UNIT, svc.BLOCK, svc.MODE, svc.MIN_CHARGE))
    prev = 0
    for upto, price in svc.TIERS:
        if upto is None:
            w.out.emit("  tier from=%d price=%d" % (prev + 1, price))
        else:
            w.out.emit("  tier from=%d upto=%d price=%d" % (prev + 1, upto, price))
            prev = upto
    w.out.emit("  allowance " + " ".join("%s=%d" % (p, svc.ALLOW[p]) for p in ORDER))


def cmd_region_list(w, cmd):
    for code in taxes.codes():
        mod = taxes.get(code)
        w.out.emit("%s %s rate=%s%% kinds=%s" % (
            code, mod.NAME, money.fmt(mod.RATE_BP, 2), ",".join(sorted(mod.TAXABLE))))
    w.out.emit("%d regions" % len(taxes.codes()))


def cmd_currency_list(w, cmd):
    for code in currencies.codes():
        cur = currencies.get(code)
        w.out.emit("%s exp=%d late_min=%s rate=%s" % (
            code, cur.EXP, money.fmt(cur.LATE_MIN, cur.EXP), money.fmt(cur.RATE_PPM, 6)))
    w.out.emit("%d currencies" % len(currencies.codes()))


def cmd_quote(w, cmd):
    cust = customers.get(w, cmd.arg(0))
    code = cmd.arg(1)
    if not services.known(code):
        raise CommandError("unknown_service", code)
    units = money.parse_int(cmd.arg(2), 1, 1000000)
    svc = services.get(code)
    cur = currencies.get(cust.currency)
    plan = cust.plan
    w.out.emit("quote %s %s plan=%s" % (cust.id, code, plan))
    for text in svc.explain(units, plan):
        w.out.emit("  " + text)
    w.out.emit("  charge %s %s" % (currencies.money_text(cur, cur.from_base(svc.quote(units, plan))),
                                  cust.currency))


def cmd_advise(w, cmd):
    cust = customers.get(w, cmd.arg(0))
    code = cmd.arg(1)
    if not services.known(code):
        raise CommandError("unknown_service", code)
    units = money.parse_int(cmd.arg(2), 1, 1000000)
    svc = services.get(code)
    rows = []
    for plan in ORDER:
        total = plans.fee(plan) + svc.rate(units, svc.ALLOW[plan])
        rows.append((total, ORDER.index(plan), plan))
    rows.sort()
    w.out.emit("advise %s %s units=%d" % (cust.id, code, units))
    for total, _, plan in rows:
        mark = " (current)" if plan == cust.plan else ""
        w.out.emit("  %s %s%s" % (plan, currencies.base_text(total), mark))
    w.out.emit("  best %s" % rows[0][2])


def cmd_region_show(w, cmd):
    code = cmd.arg(0)
    if not taxes.known(code):
        raise CommandError("unknown_region", code)
    mod = taxes.get(code)
    w.out.emit("region %s %s" % (code, mod.NAME))
    w.out.emit("  rate=%s kinds=%s" % (mod.rate_text(), mod.kinds_text()))
    gross = 11900
    w.out.emit("  inclusive %s -> net %s tax %s" % (
        money.fmt(gross, 2), money.fmt(mod.gross_to_net(gross), 2), money.fmt(mod.tax_inside(gross), 2)))
