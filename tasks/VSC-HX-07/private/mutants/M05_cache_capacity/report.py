# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Operational reports built from the audit log and the live components.

    report denials            refusals by tenant and code
    report tenant TENANT      one-screen summary of a tenant
    stats                     gateway-wide counters

All reports are sorted so that their output does not depend on the order
in which things happened to be stored: tenants by name, codes by name,
unless a report says otherwise.
"""
import lexer
import timeutil
import units
from errors import CommandError

DENY_CODES = ("auth", "nonce-required", "stale", "replay", "rate", "quota-requests",
              "quota-egress")


def _result(rec):
    for name, value in rec.fields:
        if name == "result":
            return value
    return None


def denials(world):
    """{tenant: {code: count}} over every refused request in the audit log."""
    table = {}
    for rec in world.audit.select(event="req"):
        result = _result(rec)
        if result is None or not result.startswith("deny:"):
            continue
        code = result[5:]
        row = table.setdefault(rec.tenant, {})
        row[code] = row.get(code, 0) + 1
    return table


def report_denials(world):
    table = denials(world)
    if not table:
        world.emit("denials none")
        return
    for tenant in sorted(table):
        row = table[tenant]
        parts = ["%s=%d" % (code, row[code]) for code in sorted(row)]
        world.emit("denials %s total=%d %s" % (tenant, sum(row.values()), " ".join(parts)))


def report_tenant(world, name):
    t = world.tenants.require(name)
    now = world.now
    keys = world.keys.for_tenant(t.name)
    states = {}
    for key in keys:
        st = key.state(now)
        states[st] = states.get(st, 0) + 1
    world.emit("tenant %s plan=%s created=%d status=%s" % (
        t.name, t.plan, t.created, "suspended" if t.suspended else "active"))
    world.emit("keys %s" % (" ".join("%s=%d" % (s, states[s]) for s in sorted(states)) or "none"))
    soon = [k for k in keys if k.state(now) == "active" and k.expires_at is not None]
    soon.sort(key=lambda k: (k.expires_at, k.keyid))
    for key in soon[:3]:
        world.emit("expiring %s in=%s" % (
            key.keyid, units.fmt_duration(timeutil.remaining(now, key.expires_at))))
    world.emit("quota %s" % world.quota.describe(t.name))
    entries = [e for e in world.cache.entries.values() if e.owner == t.name]
    world.emit("cache entries=%d size=%dKiB" % (len(entries), sum(e.size for e in entries)))
    queued = [j for j in world.jobs.listing() if j.tenant == t.name]
    world.emit("jobs queued=%d" % len(queued))
    row = denials(world).get(t.name, {})
    world.emit("denials total=%d" % sum(row.values()))


def cmd_report(world, cmd):
    lexer.allow_opts(cmd, ())
    if len(cmd.words) < 2:
        raise CommandError("usage: report denials | report tenant TENANT")
    sub = cmd.words[1]
    if sub == "denials":
        lexer.need(cmd, 2, 2, "report denials")
        report_denials(world)
    elif sub == "tenant":
        lexer.need(cmd, 3, 3, "report tenant TENANT")
        report_tenant(world, cmd.words[2])
    else:
        raise CommandError("report: unknown subcommand %s" % sub)


def cmd_stats(world, cmd):
    lexer.need(cmd, 1, 1, "stats")
    lexer.allow_opts(cmd, ())
    gw = world.gateway
    world.emit("stats now=%d tenants=%d served=%d refused=%d upstream=%d" % (
        world.now, len(world.tenants.all()), gw.served, gw.refused, world.backend.calls))
    world.emit("stats cache_hits=%d cache_misses=%d jobs_queued=%d audit=%d" % (
        world.cache.hits, world.cache.misses, len(world.jobs.queue), len(world.audit.records)))
