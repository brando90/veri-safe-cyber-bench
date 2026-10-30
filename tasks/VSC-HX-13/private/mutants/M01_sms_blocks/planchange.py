# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""plan set: move a customer to another plan inside the current period."""
import customers
import plans
import proration
import timeutil
from errors import CommandError


def cmd_set(w, cmd):
    cust = customers.open(w, cmd.arg(0))
    new = cmd.arg(1)
    if not plans.known(new):
        raise CommandError("unknown_plan", new)
    old = cust.plan
    if old == new:
        raise CommandError("same_plan", cust.id, new)
    days = proration.days_left(w.day)
    cust.hist.append((w.day, new))
    cust.adjust.append(customers.Adjust(timeutil.period_of(w.day), old, new, days))
    w.audit_add("plan set", cust.id, old, new)
    w.out.emit("customer %s plan %s -> %s days=%d" % (cust.id, old, new, days))
