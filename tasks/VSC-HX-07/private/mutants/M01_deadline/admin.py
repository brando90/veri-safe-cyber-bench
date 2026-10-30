# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Operator commands for looking inside the components.

    key show TENANT KEYID           one key in detail (never its secret)
    nonce list TENANT KEYID         nonces currently remembered for a key
    rate show TENANT                accepted requests inside the current window
    quota reset TENANT              start the tenant's current period afresh

These commands only read, except ``quota reset``, which is audited.
"""
import lexer
import timeutil
import units
from errors import CommandError
from output import kv


def key_show(world, tenant, keyid):
    key = world.keys.require(tenant, keyid)
    now = world.now
    world.emit("key %s state=%s issued=%d expires=%s %s" % (
        key.ident, key.state(now), key.issued, timeutil.fmt_deadline(key.expires_at),
        kv("label", key.label)))
    left = timeutil.remaining(now, key.expires_at)
    if left is not None:
        world.emit("key %s remaining=%s" % (key.ident, units.fmt_duration(left)))
    if key.revoked_at is not None:
        world.emit("key %s revoked_at=%d" % (key.ident, key.revoked_at))
    jobs = [j for j in world.jobs.listing() if j.tenant == tenant and j.keyid == keyid]
    world.emit("key %s queued_jobs=%d nonces=%d" % (
        key.ident, len(jobs), len(world.nonces.remembered(tenant, keyid, now))))


def nonce_list(world, tenant, keyid):
    world.keys.require(tenant, keyid)
    names = world.nonces.remembered(tenant, keyid, world.now)
    if not names:
        world.emit("nonces none")
        return
    world.emit("nonces %s.%s %s" % (tenant, keyid, " ".join(names)))


def rate_show(world, tenant):
    world.tenants.require(tenant)
    lim = world.limiter
    s = lim.settings(tenant)
    inside = lim.in_window(tenant, world.now, s)
    world.emit("rate %s %s in_window=%d" % (tenant, s.describe(), len(inside)))
    if s.mode == "fixed":
        start = timeutil.window_start(world.now, s.window)
        world.emit("window %d..%d" % (start, start + s.window))
    for t in inside:
        world.emit("accepted t=%d" % t)


def quota_reset(world, tenant):
    world.tenants.require(tenant)
    q = world.quota
    rec = q._current(tenant)
    before = (rec.requests, rec.egress)
    rec.requests = 0
    rec.egress = 0
    q._view.pop(tenant, None)
    world.audit.record(tenant, "quota.reset", [("requests", before[0]), ("egress", before[1])])
    world.emit("quota %s reset requests=%d egress=%dB" % (tenant, before[0], before[1]))


def cmd_nonce(world, cmd):
    lexer.need(cmd, 4, 4, "nonce list TENANT KEYID")
    lexer.allow_opts(cmd, ())
    if cmd.words[1] != "list":
        raise CommandError("nonce: unknown subcommand %s" % cmd.words[1])
    nonce_list(world, cmd.words[2], cmd.words[3])


def cmd_rate(world, cmd):
    lexer.need(cmd, 3, 3, "rate show TENANT")
    lexer.allow_opts(cmd, ())
    if cmd.words[1] != "show":
        raise CommandError("rate: unknown subcommand %s" % cmd.words[1])
    rate_show(world, cmd.words[2])


def cmd_quota(world, cmd):
    lexer.need(cmd, 3, 3, "quota reset TENANT")
    lexer.allow_opts(cmd, ())
    if cmd.words[1] != "reset":
        raise CommandError("quota: unknown subcommand %s" % cmd.words[1])
    quota_reset(world, cmd.words[2])
