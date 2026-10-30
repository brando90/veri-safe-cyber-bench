# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Per-tenant rate limiting.

The limiter remembers the times of the tenant's accepted API requests (jobs
are not rate limited).  With ``rate.mode=fixed`` it counts the accepted
requests of the current fixed window [k*W, (k+1)*W); with ``sliding`` it
counts those in (now - W, now].  A request is refused when the count has
already reached ``rate.limit``; ``retry_after`` says, in whole seconds
rounded up, when a request would next be accepted.  ``rate.limit=0``
refuses every request and gives no ``retry_after``.

Settings are read through a small per-tenant cache that is reloaded when
the configuration stamp of the tenant changes.
"""
import timeutil
import units
from errors import Deny

HISTORY = units.HOUR


class Settings:
    __slots__ = ("mode", "limit", "window")

    def __init__(self, mode, limit, window):
        self.mode = mode
        self.limit = limit
        self.window = window

    def describe(self):
        return "mode=%s limit=%d window=%s" % (self.mode, self.limit, units.fmt_duration(self.window))


def read_settings(cfg, tenant):
    """Settings straight from the configuration (no caching)."""
    return Settings(cfg.text(tenant, "rate.mode"), cfg.int_value(tenant, "rate.limit"),
                    cfg.duration_ms(tenant, "rate.window"))


class RateLimiter:
    def __init__(self, world):
        self.world = world
        self._log = {}
        self._settings = {}

    def settings(self, tenant):
        stamp = self.world.config.stamp(tenant)
        cached = self._settings.get(tenant)
        if cached is not None and cached[0] == stamp:
            return cached[1]
        s = read_settings(self.world.config, tenant)
        self._settings[tenant] = (stamp, s)
        return s

    def in_window(self, tenant, now, s):
        times = self._log.get(tenant, ())
        if s.mode == "fixed":
            return [t for t in times if timeutil.in_fixed(t, now, s.window)]
        return [t for t in times if timeutil.in_sliding(t, now, s.window)]

    def count(self, tenant, now, s=None):
        if s is None:
            s = self.settings(tenant)
        return len(self.in_window(tenant, now, s))

    def retry_after(self, s, inside, now):
        if s.mode == "fixed":
            wait = timeutil.window_end(now, s.window) - now
        else:
            # The oldest requests leave first; enough of them must leave for
            # the count to drop below the limit.
            leave = len(inside) - s.limit
            wait = inside[leave] + s.window - now
        return units.ms_to_whole_seconds(wait)

    def check(self, ctx):
        s = self.settings(ctx.tenant)
        inside = self.in_window(ctx.tenant, ctx.now, s)
        if len(inside) >= s.limit:
            if s.limit == 0:
                raise Deny("rate")
            raise Deny("rate", "retry_after=%d" % self.retry_after(s, inside, ctx.now))
        tenant, now = ctx.tenant, ctx.now

        def commit():
            log = self._log.setdefault(tenant, [])
            log.append(now)
            while log and log[0] <= now - HISTORY:
                log.pop(0)
        return commit

    def forget(self, tenant):
        self._log.pop(tenant, None)
        self._settings.pop(tenant, None)
