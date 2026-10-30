# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Per-publisher storage accounting in whole KiB."""
import perms
import policy
import units
from errors import CommandError


class Quota:
    def __init__(self, world):
        self.world = world
        self.usage = {}
        self.limits = {}

    def limit(self, user):
        return self.limits.get(user, policy.QUOTA_DEFAULT_KIB)

    def used(self, user):
        return self.usage.get(user, 0)

    def check(self, user, kib):
        if self.used(user) + kib > self.limit(user):
            raise CommandError("quota_exceeded", user, self.used(user), kib, self.limit(user))

    def adjust(self, user, delta_kib):
        n = self.used(user) + delta_kib
        if n:
            self.usage[user] = n
        else:
            self.usage.pop(user, None)


def cmd_show(w, cmd):
    target = w.users.get(cmd.arg(0))
    q = w.quota
    w.emit("quota %s used=%s limit=%s" % (target.name, units.fmt_kib(q.used(target.name)),
                                          units.fmt_kib(q.limit(target.name))))


def cmd_set(w, cmd):
    actor = w.users.actor(cmd.arg(0))
    perms.require_admin(actor)
    target = w.users.get(cmd.arg(1))
    kib = units.parse_kib(cmd.arg(2))
    w.quota.limits[target.name] = kib
    w.audit.record(actor.name, "quota.set", target.name, [("limit", kib)])
    w.emit("quota %s limit=%s" % (target.name, units.fmt_kib(kib)))
