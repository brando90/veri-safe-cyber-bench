# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Rating of one customer's metered usage for one billing period."""
import currencies
import services
import timeutil
import usage
from invoice import Line


def usage_lines(w, cust, period):
    plan = cust.plan_on(timeutil.end(period))
    cur = currencies.get(cust.currency)
    lines = []
    for code in services.codes():
        units = usage.units_in(w, cust.id, code, period)
        if units == 0:
            continue
        svc = services.get(code)
        base = svc.rate(units, svc.ALLOW[plan])
        if base <= 0:
            continue
        lines.append(Line("usage", "%s %d %s" % (code, units, svc.UNIT), cur.from_base(base), code))
    return lines
