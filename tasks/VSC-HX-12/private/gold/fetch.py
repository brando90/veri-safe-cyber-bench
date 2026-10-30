# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Downloading a release (counted per release and per package)."""
import perms
import reqs
import resolver
from errors import CommandError


def pick(w, viewer, pkg, spec):
    if spec == "" or spec.startswith("@"):
        tag = spec[1:] if spec else "latest"
        text = pkg.tags.get(tag)
        if text is None:
            if tag == "latest":
                raise CommandError("no_latest", pkg.name)
            raise CommandError("unknown_tag", pkg.name, tag)
        rel = pkg.releases[text]
        resolver.check_release(w, viewer, pkg, rel)
        return rel
    req = reqs.parse(spec)
    if req is None:
        raise CommandError("bad_req", spec)
    return resolver.best(w, viewer, pkg, [req], req.text)


def cmd_fetch(w, cmd):
    viewer = w.users.viewer(cmd.arg(0))
    pkg = w.registry.find(cmd.arg(1))
    perms.require(w, viewer, pkg, "fetch")
    rel = pick(w, viewer, pkg, cmd.arg(2, ""))
    rel.downloads += 1
    pkg.downloads += 1
    w.emit("fetched %s %s%s" % (pkg.name, rel.text, resolver.notes(rel)))
