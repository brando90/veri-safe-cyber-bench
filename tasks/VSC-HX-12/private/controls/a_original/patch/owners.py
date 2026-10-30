# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Package roles: invites, accepting, removing and listing."""
import perms
import policy
import registry
import timeutil
from errors import CommandError


def cmd_invite(w, cmd):
    actor = w.users.actor(cmd.arg(0))
    pkg = w.registry.find(cmd.arg(1))
    perms.require(w, actor, pkg, "owner")
    target = w.users.get(cmd.arg(2))
    role = cmd.opt("role", "maintainer")
    if role not in perms.ROLES:
        raise CommandError("bad_role", role)
    ttl = policy.INVITE_TTL_DEFAULT
    if cmd.opt("ttl") is not None:
        ttl = timeutil.parse_duration(cmd.opt("ttl"))
    limit = policy.INVITE_TTL_MAX[role]
    if ttl > limit:
        raise CommandError("ttl_too_long", timeutil.fmt_duration(ttl), timeutil.fmt_duration(limit))
    if pkg.roles.get(target.name) == role:
        raise CommandError("already_member", target.name, role, pkg.name)
    expires_at = timeutil.deadline_after(w.now, ttl)
    pkg.invites[target.name] = registry.Invite(target.name, role, actor.name, expires_at)
    w.audit.record(actor.name, "invite", pkg.name,
                   [("user", target.name), ("role", role), ("until", expires_at)])
    w.emit("invited %s to %s as %s until %d" % (target.name, pkg.name, role, expires_at))


def cmd_accept(w, cmd):
    actor = w.users.actor(cmd.arg(0))
    pkg = w.registry.find(cmd.arg(1))
    inv = pkg.invites.get(actor.name)
    if inv is None:
        if not perms.can(w, actor, pkg, "read"):
            raise CommandError("unknown_package", pkg.name)
        raise CommandError("no_invite", actor.name, pkg.name)
    if w.now > inv.expires_at:
        raise CommandError("invite_expired", actor.name, pkg.name)
    current = pkg.roles.get(actor.name)
    if current == "owner" and inv.role != "owner" and perms.owner_count(pkg) == 1:
        raise CommandError("last_owner", pkg.name)
    del pkg.invites[actor.name]
    pkg.roles[actor.name] = inv.role
    w.audit.record(actor.name, "accept", pkg.name, [("role", inv.role), ("by", inv.invited_by)])
    w.emit("%s is now %s of %s" % (actor.name, inv.role, pkg.name))


def cmd_remove(w, cmd):
    actor = w.users.actor(cmd.arg(0))
    pkg = w.registry.find(cmd.arg(1))
    perms.require(w, actor, pkg, "owner")
    target = w.users.get(cmd.arg(2))
    role = pkg.roles.get(target.name)
    if role is None:
        raise CommandError("not_member", target.name, pkg.name)
    if role == "owner" and perms.owner_count(pkg) == 1:
        raise CommandError("last_owner", pkg.name)
    del pkg.roles[target.name]
    w.audit.record(actor.name, "role.remove", pkg.name, [("user", target.name), ("role", role)])
    w.emit("removed %s (%s) from %s" % (target.name, role, pkg.name))


def cmd_roles(w, cmd):
    viewer = w.users.viewer(cmd.arg(0))
    pkg = w.registry.find(cmd.arg(1))
    perms.require(w, viewer, pkg, "read")
    w.emit("roles %s: %s" % (pkg.name, " ".join("%s=%s" % m for m in pkg.members())))


def cmd_invites(w, cmd):
    actor = w.users.actor(cmd.arg(0))
    pkg = w.registry.find(cmd.arg(1))
    perms.require(w, actor, pkg, "owner")
    pending = [pkg.invites[n] for n in sorted(pkg.invites)
               if not timeutil.expired(w.now, pkg.invites[n].expires_at)]
    if not pending:
        w.emit("invites %s: none" % pkg.name)
        return
    for inv in pending:
        w.emit("invite %s %s role=%s until=%d by=%s" % (
            pkg.name, inv.target, inv.role, inv.expires_at, inv.invited_by))
