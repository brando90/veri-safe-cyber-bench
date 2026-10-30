# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The program's own consistency check.

``after_commit`` runs whenever a request or job has just been accepted and
recorded; ``full_check`` runs after every command and on ``check``.  Both
read the configuration directly (never through a component's cached copy)
and raise InvariantViolation when a documented rule does not hold; the
dispatcher then prints ``INVARIANT: ...`` on standard error and exits 86.
"""
import quota as quota_mod
import ratelimit
import units
from errors import InvariantViolation


def require(cond, message):
    if not cond:
        raise InvariantViolation(message)


def after_commit(world, ctx):
    cfg = world.config
    tenant = ctx.tenant
    used = world.quota.peek(tenant)
    lim = quota_mod.read_limits(cfg, tenant)
    require(used.requests <= lim.requests,
            "quota: %s has %d requests in the period, limit %d" % (tenant, used.requests, lim.requests))
    require(used.egress <= lim.egress,
            "quota: %s has %d egress bytes in the period, limit %d" % (tenant, used.egress, lim.egress))
    if ctx.kind == "api":
        s = ratelimit.read_settings(cfg, tenant)
        n = len(world.limiter.in_window(tenant, ctx.now, s))
        require(n <= s.limit, "rate: %s has %d requests in the window, limit %d" % (tenant, n, s.limit))


def full_check(world):
    cache = world.cache
    total = sum(e.size for e in cache.entries.values())
    require(total == cache.used, "cache: accounted %d KiB, entries hold %d KiB" % (cache.used, total))
    for entry in cache.entries.values():
        require(entry.size == units.kib_ceil(entry.nbytes), "cache: entry %s mis-sized" % entry.key)
    seen = set()
    for job in world.jobs.listing():
        require(job.state == "queued", "jobs: %s is %s but still queued" % (job.id, job.state))
        require(job.id not in seen, "jobs: %s queued twice" % job.id)
        seen.add(job.id)
    for tenant in world.meter.tenants():
        u = world.meter.usage(tenant)
        require(u.egress_kib >= units.kib_ceil(u.egress_bytes),
                "meter: %s egress KiB below byte total" % tenant)
