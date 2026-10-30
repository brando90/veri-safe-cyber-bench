# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Yank, unyank, deprecate, unpublish, prune, delete and visibility."""
import output
import perms
import policy
import timeutil
import units
from errors import CommandError


def _target(w, cmd, action):
    actor = w.users.actor(cmd.arg(0))
    pkg = w.registry.find(cmd.arg(1))
    perms.require(w, actor, pkg, action)
    return actor, pkg


def cmd_yank(w, cmd):
    actor, pkg = _target(w, cmd, "yank")
    rel = pkg.release(cmd.arg(2))
    if rel.yanked:
        raise CommandError("already_yanked", pkg.name, rel.text)
    rel.yanked = True
    rel.yank_reason = cmd.opt("reason", "")
    pkg.recompute_latest()
    w.audit.record(actor.name, "yank", pkg.name, [("version", rel.text), ("reason", rel.yank_reason)])
    w.emit("yanked %s %s" % (pkg.name, rel.text))


def cmd_unyank(w, cmd):
    actor, pkg = _target(w, cmd, "unyank")
    rel = pkg.release(cmd.arg(2))
    if not rel.yanked:
        raise CommandError("not_yanked", pkg.name, rel.text)
    rel.yanked = False
    rel.yank_reason = ""
    pkg.recompute_latest()
    w.audit.record(actor.name, "unyank", pkg.name, [("version", rel.text)])
    w.emit("unyanked %s %s" % (pkg.name, rel.text))


def cmd_deprecate(w, cmd):
    actor, pkg = _target(w, cmd, "deprecate")
    rel = pkg.release(cmd.arg(2))
    message = cmd.opt("message", "")
    rel.deprecated = message or None
    w.audit.record(actor.name, "deprecate", pkg.name, [("version", rel.text), ("message", message)])
    if message:
        w.emit("deprecated %s %s" % (pkg.name, rel.text))
    else:
        w.emit("undeprecated %s %s" % (pkg.name, rel.text))


def cmd_unpublish(w, cmd):
    actor, pkg = _target(w, cmd, "unpublish")
    rel = pkg.release(cmd.arg(2))
    grace = policy.UNPUBLISH_GRACE["prerelease" if rel.ver.pre else "stable"]
    if timeutil.expired(w.now, timeutil.deadline_after(rel.published_at, grace)):
        raise CommandError("grace_over", pkg.name, rel.text, rel.published_at)
    del pkg.releases[rel.text]
    pkg.recompute_latest()
    pkg.burned.add(rel.text)
    w.quota.adjust(rel.publisher, -units.kib_ceil(rel.size))
    w.audit.record(actor.name, "unpublish", pkg.name, [("version", rel.text)])
    w.emit("unpublished %s %s" % (pkg.name, rel.text))


def cmd_prune(w, cmd):
    actor = w.users.actor(cmd.arg(0))
    perms.require_admin(actor)
    pkg = w.registry.find(cmd.arg(1))
    gone = [rel for rel in pkg.sorted_releases() if rel.yanked]
    for rel in gone:
        pkg.drop_release(rel.text)
        pkg.burned.add(rel.text)
        w.quota.adjust(rel.publisher, -units.kib_ceil(rel.size))
    texts = [rel.text for rel in gone]
    w.audit.record(actor.name, "prune", pkg.name, [("versions", output.join_names(texts))])
    w.emit("pruned %s: %s" % (pkg.name, ", ".join(texts) if texts else "nothing"))


def cmd_delete(w, cmd):
    actor = w.users.actor(cmd.arg(0))
    perms.require_admin(actor)
    pkg = w.registry.find(cmd.arg(1))
    for rel in pkg.sorted_releases():
        w.quota.adjust(rel.publisher, -units.kib_ceil(rel.size))
    w.registry.delete(pkg)
    w.audit.record(actor.name, "package.delete", pkg.name, [("releases", len(pkg.releases))])
    w.emit("deleted %s (%d releases)" % (pkg.name, len(pkg.releases)))


def cmd_visibility(w, cmd):
    actor, pkg = _target(w, cmd, "visibility")
    value = cmd.arg(2)
    if value not in ("public", "private"):
        raise CommandError("bad_visibility", value)
    pkg.visibility = value
    w.audit.record(actor.name, "visibility", pkg.name, [("value", value)])
    w.emit("%s is now %s" % (pkg.name, value))
