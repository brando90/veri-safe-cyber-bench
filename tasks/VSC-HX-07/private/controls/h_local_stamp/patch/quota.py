# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Per-tenant quotas over a period.

Periods are fixed windows of length ``quota.period`` counted from time 0.
Two counters are kept per tenant and period: accepted requests (API requests
and successful job runs) and egress bytes.  A request is refused with
``quota-requests`` when one more would exceed ``quota.requests``, and with
``quota-egress`` when its response would take the egress above
``quota.egress``; reaching a limit exactly is allowed.  Changing
``quota.period`` starts a new period.

Counters are read through a per-command view: the dispatcher calls
``begin_command`` before every command, so that every read during one
command sees the same period even when a long batch of jobs is processed.
"""
import timeutil
import units
from errors import Deny


class Counters:
    __slots__ = ("period", "requests", "egress")

    def __init__(self, period, requests=0, egress=0):
        self.period = period
        self.requests = requests
        self.egress = egress

    def copy(self):
        return Counters(self.period, self.requests, self.egress)


class Limits:
    __slots__ = ("requests", "egress", "period")

    def __init__(self, requests, egress, period):
        self.requests = requests
        self.egress = egress
        self.period = period


def read_limits(cfg, tenant):
    return Limits(cfg.int_value(tenant, "quota.requests"), cfg.size_bytes(tenant, "quota.egress"),
                  cfg.duration_ms(tenant, "quota.period"))


class Quota:
    def __init__(self, world):
        self.world = world
        self._store = {}
        self._view = {}
        self._limits = {}
        self._now = 0

    # ------------------------------------------------------------ limits
    def limits(self, tenant):
        stamp = self.world.config.stamp(tenant)
        cached = self._limits.get(tenant)
        if cached is not None and cached[0] == stamp:
            return cached[1]
        lim = read_limits(self.world.config, tenant)
        self._limits[tenant] = (stamp, lim)
        return lim

    # ------------------------------------------------------------ counters
    def begin_command(self, now):
        self._now = now
        self._view.clear()

    def _period_key(self, tenant):
        width = self.limits(tenant).period
        return (width, timeutil.window_index(self._now, width))

    def _current(self, tenant):
        """The stored counters of TENANT for the current period (rolled over if needed)."""
        key = self._period_key(tenant)
        rec = self._store.get(tenant)
        if rec is None or rec.period != key:
            rec = Counters(key)
            self._store[tenant] = rec
        return rec

    def counters(self, tenant):
        """Read-only snapshot of TENANT's counters for this command."""
        snap = self._view.get(tenant)
        if snap is None:
            snap = self._current(tenant).copy()
            self._view[tenant] = snap
        return snap

    def peek(self, tenant):
        """The stored counters, bypassing the view (consistency checks)."""
        return self._current(tenant).copy()

    # ------------------------------------------------------------ admission
    def check_requests(self, ctx):
        lim = self.limits(ctx.tenant)
        if self.counters(ctx.tenant).requests + 1 > lim.requests:
            raise Deny("quota-requests")

    def check_egress(self, ctx, nbytes):
        lim = self.limits(ctx.tenant)
        if self.counters(ctx.tenant).egress + nbytes > lim.egress:
            raise Deny("quota-egress")

    def commit(self, tenant, nbytes):
        rec = self._current(tenant)
        rec.requests += 1
        rec.egress += nbytes
        self._view.pop(tenant, None)

    # ------------------------------------------------------------ reporting
    def describe(self, tenant):
        c = self.counters(tenant)
        lim = self.limits(tenant)
        return "period=%d requests=%d/%d egress=%dB/%s" % (
            c.period[1], c.requests, lim.requests, c.egress, units.fmt_size(lim.egress))
