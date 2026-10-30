# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Choosing a release for one or more requirements."""
import perms
import policy
import reqs
import timeutil
from errors import CommandError


def bypasses_embargo(viewer, pkg):
    return perms.role_of(pkg, viewer) in policy.EMBARGO_BYPASS_ROLES


def under_embargo(w, viewer, pkg, rel):
    if rel.embargo_until is None or bypasses_embargo(viewer, pkg):
        return False
    return not timeutil.expired(w.now, rel.embargo_until)


def selectable(req, rel):
    if not reqs.matches(req, rel.ver):
        return False
    if rel.yanked and req.kind not in policy.YANKED_SELECTABLE:
        return False
    return True


def best(w, viewer, pkg, req_list, label):
    """The highest release of PKG that every requirement selects."""
    found = None
    held = None
    for rel in pkg.sorted_releases():
        if not all(selectable(req, rel) for req in req_list):
            continue
        if under_embargo(w, viewer, pkg, rel):
            held = rel
            continue
        found = rel
    if found is None:
        if held is not None:
            raise CommandError("embargoed", pkg.name, held.text, held.embargo_until)
        raise CommandError("no_match", pkg.name, label)
    return found


def check_release(w, viewer, pkg, rel):
    if under_embargo(w, viewer, pkg, rel):
        raise CommandError("embargoed", pkg.name, rel.text, rel.embargo_until)


def notes(rel):
    out = ""
    if rel.yanked:
        out += " (yanked)"
    if rel.deprecated:
        out += " (deprecated: %s)" % rel.deprecated
    return out


def cmd_resolve(w, cmd):
    viewer = w.users.viewer(cmd.arg(0))
    pkg = w.registry.find(cmd.arg(1))
    perms.require(w, viewer, pkg, "read")
    spec = cmd.arg(2)
    req = reqs.parse(spec)
    if req is None:
        raise CommandError("bad_req", spec)
    rel = best(w, viewer, pkg, [req], req.text)
    w.emit("%s %s -> %s%s" % (pkg.name, req.text, rel.text, notes(rel)))
