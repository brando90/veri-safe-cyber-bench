# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""usage batch: several quantities for one service in one command."""
import customers
import money
import usage
from errors import CommandError


def cmd_batch(w, cmd):
    cmd.allow("day", "id")
    cust = customers.open(w, cmd.arg(0))
    svc = cmd.arg(1)
    usage.check_service(svc)
    if len(cmd.args) < 3:
        raise CommandError("bad_batch")
    quantities = [money.parse_int(t, 1, usage.UNITS_MAX) for t in cmd.args[2:]]
    day = usage.parse_day(w, cmd.opt("day"))
    usage.check_day(w, cust, day)
    prefix = cmd.opt("id")
    keys = []
    rids = []
    if prefix is not None:
        for i in range(len(quantities)):
            rid = "%s-%d" % (prefix, i + 1)
            usage.check_id(rid)
            k = (svc, rid)
            if k in w.usage_ids or k in keys:
                raise CommandError("duplicate_usage", rid)
            keys.append(k)
            rids.append(rid)
    for i, units in enumerate(quantities):
        usage.add(w, cust, svc, units, day, rids[i] if rids else None)
    w.usage_ids.update(keys)
    w.out.emit("usage %s %s batch=%d total=%d day=%d"
               % (cust.id, svc, len(quantities), sum(quantities), day))
