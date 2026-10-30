# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Rankings and search."""
import names
import perms
import policy
import units
from errors import CommandError


def rank(rows, n):
    return sorted(rows, key=lambda r: (-r[1], r[0]))[:n]


def visible(w, viewer):
    return [p for p in w.registry.sorted() if perms.can(w, viewer, p, "read")]


def dependents_of(w, viewer, pkg):
    return [p for p in visible(w, viewer) if p is not pkg and p.depends_on(pkg.key)]


def _top_n(cmd):
    n = units.parse_kib(cmd.opt("n", str(policy.TOP_DEFAULT)))
    return max(1, min(n, policy.TOP_MAX))


def cmd_top(w, cmd):
    viewer = w.users.viewer(cmd.arg(0))
    kind = cmd.arg(1)
    n = _top_n(cmd)
    pkgs = visible(w, viewer)
    show = str
    if kind == "downloads":
        rows = rank([(p.name, p.downloads) for p in pkgs], n)
    elif kind == "releases":
        rows = rank([(p.name, len(p.releases)) for p in pkgs], n)
    elif kind == "dependents":
        rows = rank([(p.name, len(dependents_of(w, viewer, p))) for p in pkgs], n)
    elif kind == "size":
        rows = sorted(((p.name, p.total_kib()) for p in pkgs),
                      key=lambda r: (r[1], r[0]), reverse=True)[:n]
        show = units.fmt_kib
    else:
        raise CommandError("bad_report", kind)
    w.emit("top %s:" % kind)
    if not rows:
        w.emit("  (none)")
    for i, (name, value) in enumerate(rows, 1):
        w.emit("  %d. %s %s" % (i, name, show(value)))


def cmd_search(w, cmd):
    viewer = w.users.viewer(cmd.arg(0))
    text = cmd.arg(1)
    needle = names.canonical(text)
    hits = [p for p in visible(w, viewer) if needle in p.key]
    if not hits:
        w.emit("search %s: no packages" % text)
        return
    for p in hits:
        w.emit("found %s latest=%s releases=%d" % (p.name, p.tags.get("latest", "-"), len(p.releases)))
