# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Publishing a release."""
import names
import perms
import registry
import reqs
import semver
import timeutil
import units
from errors import CommandError

VISIBILITIES = ("public", "private")


def parse_deps(w, actor, text, pkg_name):
    if not text:
        return []
    deps = []
    seen = set()
    own_key = names.canonical(pkg_name)
    for part in text.split(";"):
        name, sep, spec = part.strip().partition("@")
        if not sep or not names.valid_package(name):
            raise CommandError("bad_deps", text)
        req = reqs.parse(spec)
        if req is None:
            raise CommandError("bad_req", spec)
        key = names.canonical(name)
        if key == own_key:
            raise CommandError("self_dep", pkg_name)
        if key in seen:
            raise CommandError("bad_deps", text)
        seen.add(key)
        target = w.registry.find(name)
        perms.require(w, actor, target, "read")
        deps.append(registry.Dependency(target.name, req))
    return deps


def cmd_publish(w, cmd):
    actor = w.users.actor(cmd.arg(0))
    name = cmd.arg(1)
    vtext = cmd.arg(2)
    ver = semver.parse(vtext)
    if ver is None:
        raise CommandError("bad_version", vtext)
    size = units.parse_size(cmd.opt("size", "0"))
    embargo_until = None
    if cmd.opt("embargo") is not None:
        embargo_until = timeutil.deadline_after(w.now, timeutil.parse_duration(cmd.opt("embargo")))
    visibility = cmd.opt("visibility", "public")
    if visibility not in VISIBILITIES:
        raise CommandError("bad_visibility", visibility)

    pkg = w.registry.lookup(name)
    if pkg is None:
        names.check_new_package(name)
    else:
        perms.require(w, actor, pkg, "publish")
        if ver.text in pkg.releases:
            raise CommandError("version_exists", pkg.name, ver.text)
        if ver.text in pkg.burned:
            raise CommandError("version_burned", pkg.name, ver.text)
    deps = parse_deps(w, actor, cmd.opt("deps"), name)
    kib = units.kib_ceil(size)
    w.quota.check(actor.name, kib)

    if pkg is None:
        pkg = w.registry.create(name, actor.name, w.now, visibility)
    rel = registry.Release(ver, size, deps, actor.name, w.now, embargo_until)
    pkg.releases[ver.text] = rel
    w.quota.adjust(actor.name, kib)
    cur = pkg.tags.get("latest")
    if not ver.pre and (cur is None or semver.key(ver) > semver.key(pkg.releases[cur].ver)):
        pkg.tags["latest"] = ver.text

    detail = [("version", ver.text), ("size", size)]
    if deps:
        detail.append(("deps", ";".join(str(d) for d in deps)))
    if embargo_until is not None:
        detail.append(("embargo", embargo_until))
    w.audit.record(actor.name, "publish", pkg.name, detail)
    w.emit("published %s %s (%s)" % (pkg.name, ver.text, units.fmt_kib(kib)))
