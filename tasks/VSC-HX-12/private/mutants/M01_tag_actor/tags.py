# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Distribution tags (``beta``, ``next``, ...) and the tag commands."""
import names
import perms
from errors import CommandError

MANAGED = frozenset({"latest"})


def _change(w, cmd):
    actor = w.users.get(cmd.arg(0))
    pkg = w.registry.find(cmd.arg(1))
    tag = cmd.arg(2)
    if not names.valid_tag(tag):
        raise CommandError("bad_tag", tag)
    if tag in MANAGED:
        raise CommandError("managed_tag", tag)
    perms.require(w, actor, pkg, "tag")
    return actor, pkg, tag


def cmd_add(w, cmd):
    actor, pkg, tag = _change(w, cmd)
    rel = pkg.release(cmd.arg(3))
    old = pkg.tags.get(tag)
    pkg.tags[tag] = rel.text
    detail = [("tag", tag), ("version", rel.text)]
    if old is not None:
        detail.append(("was", old))
    w.audit.record(actor.name, "tag.add", pkg.name, detail)
    w.emit("tag %s %s -> %s" % (pkg.name, tag, rel.text))


def cmd_rm(w, cmd):
    actor, pkg, tag = _change(w, cmd)
    if tag not in pkg.tags:
        raise CommandError("unknown_tag", pkg.name, tag)
    old = pkg.tags.pop(tag)
    w.audit.record(actor.name, "tag.rm", pkg.name, [("tag", tag), ("was", old)])
    w.emit("tag %s %s removed" % (pkg.name, tag))


def cmd_list(w, cmd):
    viewer = w.users.viewer(cmd.arg(0))
    pkg = w.registry.find(cmd.arg(1))
    perms.require(w, viewer, pkg, "read")
    if not pkg.tags:
        w.emit("tags %s: none" % pkg.name)
        return
    w.emit("tags %s: %s" % (pkg.name, " ".join(
        "%s=%s" % (t, pkg.tags[t]) for t in sorted(pkg.tags))))
