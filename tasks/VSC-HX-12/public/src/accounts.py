# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The user commands."""
import output
import perms
from errors import CommandError


def cmd_add(w, cmd):
    name = cmd.arg(0)
    flag = cmd.arg(1, "")
    if flag not in ("", "admin"):
        raise CommandError("usage", cmd.usage)
    user = w.users.add(name, flag == "admin")
    w.audit.record("-", "user.add", user.name, [("admin", "yes" if user.admin else "no")])
    w.emit("user %s added%s" % (user.name, " (admin)" if user.admin else ""))


def cmd_disable(w, cmd):
    actor = w.users.actor(cmd.arg(0))
    perms.require_admin(actor)
    target = w.users.get(cmd.arg(1))
    if target.disabled:
        raise CommandError("disabled", target.name)
    target.disabled = True
    w.audit.record(actor.name, "user.disable", target.name)
    w.emit("user %s disabled" % target.name)


def cmd_enable(w, cmd):
    actor = w.users.actor(cmd.arg(0))
    perms.require_admin(actor)
    target = w.users.get(cmd.arg(1))
    if not target.disabled:
        raise CommandError("not_disabled", target.name)
    target.disabled = False
    w.audit.record(actor.name, "user.enable", target.name)
    w.emit("user %s enabled" % target.name)


def cmd_remove(w, cmd):
    actor = w.users.actor(cmd.arg(0))
    perms.require_admin(actor)
    target = w.users.get(cmd.arg(1))
    dropped = []
    for pkg in w.registry.sorted():
        if pkg.roles.pop(target.name, None) is not None:
            dropped.append(pkg.name)
        pkg.invites.pop(target.name, None)
    w.users.remove(target.name)
    w.audit.record(actor.name, "user.remove", target.name, [("roles", output.join_names(dropped))])
    w.emit("user %s removed" % target.name)


def cmd_show(w, cmd):
    target = w.users.get(cmd.arg(0))
    roles = ["%s:%s" % (pkg.name, pkg.roles[target.name])
             for pkg in w.registry.sorted() if target.name in pkg.roles]
    w.emit("user %s admin=%s state=%s roles=%s" % (
        target.name, "yes" if target.admin else "no",
        "disabled" if target.disabled else "active", output.join_names(roles)))
