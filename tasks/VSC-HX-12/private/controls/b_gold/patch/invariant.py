# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The program's own consistency check.

``full_check`` runs after every command and on ``check``.  A failure raises
InvariantViolation; main prints ``INVARIANT: ...`` on standard error and
exits 86.
"""
import perms
import units
from errors import InvariantViolation


def require(cond, message):
    if not cond:
        raise InvariantViolation(message)


def check_package(w, pkg, held):
    require(perms.owner_count(pkg) >= 1, "package %s has no owner" % pkg.name)
    for user, role in pkg.roles.items():
        require(user in w.users.by_name, "role holder %s of %s is not a user" % (user, pkg.name))
        require(role in perms.LEVEL, "bad role %s on %s" % (role, pkg.name))
    for tag, text in pkg.tags.items():
        require(text in pkg.releases, "tag %s of %s points to missing release %s"
                % (tag, pkg.name, text))
    require(not (set(pkg.releases) & pkg.burned), "%s has a burned release" % pkg.name)
    total = 0
    for rel in pkg.releases.values():
        held[rel.publisher] = held.get(rel.publisher, 0) + units.kib_ceil(rel.size)
        total += rel.downloads
    require(total <= pkg.downloads, "download count of %s is behind" % pkg.name)


def full_check(w):
    held = {}
    for pkg in w.registry.packages.values():
        check_package(w, pkg, held)
    for user in sorted(set(held) | set(w.quota.usage)):
        require(w.quota.used(user) == held.get(user, 0),
                "storage of %s is %d KiB, releases hold %d KiB"
                % (user, w.quota.used(user), held.get(user, 0)))


def cmd_check(w, cmd):
    full_check(w)
    w.emit("check ok (%d users, %d packages)" % (len(w.users.by_name), len(w.registry.packages)))
