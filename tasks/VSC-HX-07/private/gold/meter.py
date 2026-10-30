# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Usage metering for billing.

Every accepted API request and every successful job run is metered for its
tenant, whether the response came from the upstream service or from the
cache.  Egress is metered per response, rounded up to whole KiB (a 1-byte
response counts as 1 KiB, a 0-byte response as 0 KiB); the exact byte
total is kept as well for reports.  Meter totals are lifetime totals, they
do not follow the quota period.
"""
import lexer
import units


class Usage:
    __slots__ = ("api", "jobs", "egress_bytes", "egress_kib")

    def __init__(self):
        self.api = 0
        self.jobs = 0
        self.egress_bytes = 0
        self.egress_kib = 0

    @property
    def requests(self):
        return self.api + self.jobs


class Meter:
    def __init__(self, world):
        self.world = world
        self._usage = {}

    def usage(self, tenant):
        return self._usage.setdefault(tenant, Usage())

    def record(self, tenant, kind, nbytes):
        u = self.usage(tenant)
        if kind == "api":
            u.api += 1
        else:
            u.jobs += 1
        u.egress_bytes += nbytes
        u.egress_kib += units.kib_ceil(nbytes)

    def tenants(self):
        return sorted(self._usage)


def cmd_top(world, cmd):
    """Tenants by metered requests, most first; ties by name."""
    lexer.need(cmd, 1, 1, "top")
    lexer.allow_opts(cmd, ())
    rows = [(world.meter.usage(t.name), t.name) for t in world.tenants.all()]
    rows.sort(key=lambda r: (-r[0].requests, r[1]))
    if not rows:
        world.emit("top none")
    for rank, (u, name) in enumerate(rows, 1):
        world.emit("%d %s requests=%d egress=%dB" % (rank, name, u.requests, u.egress_bytes))


def cmd_usage(world, cmd):
    lexer.need(cmd, 2, 2, "usage TENANT")
    lexer.allow_opts(cmd, ())
    tenant = world.tenants.require(cmd.words[1]).name
    world.emit("usage %s %s" % (tenant, world.quota.describe(tenant)))
    s = world.limiter.settings(tenant)
    world.emit("rate %s %s in_window=%d" % (tenant, s.describe(),
                                            world.limiter.count(tenant, world.now, s)))
    u = world.meter.usage(tenant)
    world.emit("meter %s api=%d jobs=%d egress=%dB" % (tenant, u.api, u.jobs, u.egress_bytes))
