# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Tenants: the customers of the gateway.  Every key, counter, cache entry,
job and bill belongs to exactly one tenant."""
import re

import lexer
import plans
from errors import CommandError

NAME_RE = re.compile(r"[a-z][a-z0-9-]{0,15}\Z")


class Tenant:
    __slots__ = ("name", "plan", "created", "suspended")

    def __init__(self, name, plan, created):
        self.name = name
        self.plan = plan
        self.created = created
        self.suspended = False


class Tenants:
    def __init__(self, world):
        self.world = world
        self._by_name = {}

    def get(self, name):
        return self._by_name.get(name)

    def require(self, name):
        t = self._by_name.get(name)
        if t is None:
            raise CommandError("unknown tenant %s" % name)
        return t

    def all(self):
        return [self._by_name[n] for n in sorted(self._by_name)]

    def add(self, name, plan):
        if not NAME_RE.match(name):
            raise CommandError("tenant: bad name %s (a-z, 0-9 and '-', at most 16, starting with a letter)" % name)
        if name in self._by_name:
            raise CommandError("tenant: %s already exists" % name)
        if plan not in plans.PLANS:
            raise CommandError("tenant: unknown plan %s" % plan)
        t = Tenant(name, plan, self.world.now)
        self._by_name[name] = t
        self.world.audit.record(name, "tenant.add", [("plan", plan)])
        return t

    def change_plan(self, name, plan):
        t = self.require(name)
        if plan not in plans.PLANS:
            raise CommandError("tenant: unknown plan %s" % plan)
        old = t.plan
        t.plan = plan
        self.world.audit.record(name, "tenant.plan", [("from", old), ("to", plan)])
        return t

    def set_suspended(self, name, flag):
        t = self.require(name)
        t.suspended = flag
        self.world.audit.record(name, "tenant.suspend" if flag else "tenant.resume", [])
        return t


def cmd_tenant(world, cmd):
    if len(cmd.words) < 2:
        raise CommandError("usage: tenant add|plan|suspend|resume|list ...")
    sub = cmd.words[1]
    reg = world.tenants
    if sub == "add":
        lexer.need(cmd, 3, 3, "tenant add NAME [plan=PLAN]")
        lexer.allow_opts(cmd, ("plan",))
        t = reg.add(cmd.words[2], cmd.opt("plan", plans.DEFAULT_PLAN))
        world.emit("tenant %s plan=%s" % (t.name, t.plan))
    elif sub == "plan":
        lexer.need(cmd, 4, 4, "tenant plan NAME PLAN")
        lexer.allow_opts(cmd, ())
        t = reg.change_plan(cmd.words[2], cmd.words[3])
        world.emit("tenant %s plan=%s" % (t.name, t.plan))
    elif sub in ("suspend", "resume"):
        lexer.need(cmd, 3, 3, "tenant %s NAME" % sub)
        lexer.allow_opts(cmd, ())
        t = reg.set_suspended(cmd.words[2], sub == "suspend")
        world.emit("tenant %s %s" % (t.name, "suspended" if t.suspended else "active"))
    elif sub == "list":
        lexer.need(cmd, 2, 2, "tenant list")
        lexer.allow_opts(cmd, ())
        if not reg.all():
            world.emit("tenants none")
        for t in reg.all():
            keys = world.keys.for_tenant(t.name)
            active = sum(1 for k in keys if k.state(world.now) == "active")
            world.emit("tenant %s plan=%s keys=%d active=%d%s" % (
                t.name, t.plan, len(keys), active, " suspended" if t.suspended else ""))
    else:
        raise CommandError("tenant: unknown subcommand %s" % sub)
