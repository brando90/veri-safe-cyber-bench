# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Package details and reverse dependencies."""
import output
import perms
import units


def release_line(rel):
    parts = ["  %s" % rel.text, units.fmt_bytes(rel.size), "by=%s" % rel.publisher,
             "at=%d" % rel.published_at]
    if rel.deps:
        parts.append("deps=" + ";".join(str(d) for d in rel.deps))
    if rel.embargo_until is not None:
        parts.append("embargo=%d" % rel.embargo_until)
    if rel.yanked:
        parts.append(output.kv("yanked", rel.yank_reason))
    if rel.deprecated:
        parts.append(output.kv("deprecated", rel.deprecated))
    if rel.downloads:
        parts.append("downloads=%d" % rel.downloads)
    return " ".join(parts)


def cmd_info(w, cmd):
    viewer = w.users.viewer(cmd.arg(0))
    pkg = w.registry.find(cmd.arg(1))
    perms.require(w, viewer, pkg, "read")
    w.emit("package %s visibility=%s latest=%s downloads=%d releases=%d" % (
        pkg.name, pkg.visibility, pkg.tags.get("latest", "-"), pkg.downloads, len(pkg.releases)))
    for rel in pkg.sorted_releases():
        w.emit(release_line(rel))


def cmd_dependents(w, cmd):
    viewer = w.users.viewer(cmd.arg(0))
    pkg = w.registry.find(cmd.arg(1))
    perms.require(w, viewer, pkg, "read")
    users = []
    for other in w.registry.sorted():
        if other is pkg or not other.depends_on(pkg.key):
            continue
        users.append(other.name)
    w.emit("dependents %s: %s" % (pkg.name, " ".join(users) if users else "none"))
