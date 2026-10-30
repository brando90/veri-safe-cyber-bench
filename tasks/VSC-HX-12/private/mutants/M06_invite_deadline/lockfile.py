# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Lockfiles: one release per package for a set of roots and their
dependencies, stored under a name."""
import hashlib

import perms
import reqs
import resolver
from errors import CommandError

MAX_ROUNDS = 32


class Lock:
    __slots__ = ("name", "viewer", "roots", "entries", "digest", "made_at")

    def __init__(self, name, viewer, roots, entries, made_at):
        self.name = name
        self.viewer = viewer
        self.roots = roots
        self.entries = entries
        self.digest = digest(entries)
        self.made_at = made_at


def digest(entries):
    text = "".join("%s %s\n" % (key, ver) for key, ver in entries)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def parse_roots(w, viewer, texts):
    roots = []
    for text in texts:
        name, sep, spec = text.partition("@")
        if not sep or not name:
            raise CommandError("bad_root", text)
        pkg = w.registry.find(name)
        perms.require(w, viewer, pkg, "read")
        req = reqs.parse(spec)
        if req is None:
            raise CommandError("bad_req", spec)
        roots.append((pkg, req, "root"))
    return roots


def solve(w, viewer, roots):
    chosen = {}
    for _ in range(MAX_ROUNDS):
        want = {}
        for pkg, req, origin in roots:
            want.setdefault(pkg.key, []).append((req, origin))
        for key in sorted(chosen):
            rel = chosen[key]
            parent = w.registry.packages[key]
            for dep in rel.deps:
                want.setdefault(dep.key, []).append((dep.req, "%s@%s" % (parent.name, rel.text)))
        new = {}
        for key in sorted(want):
            pkg = w.registry.find(key)
            perms.require(w, viewer, pkg, "read")
            req_list = [req for req, _ in want[key]]
            try:
                new[key] = resolver.best(w, viewer, pkg, req_list, req_list[0].text)
            except CommandError as exc:
                if exc.code != "no_match" or len(req_list) < 2:
                    raise
                why = "; ".join("%s from %s" % (req.text, origin) for req, origin in want[key])
                raise CommandError("conflict", pkg.name, why)
        if new == chosen:
            return chosen
        chosen = new
    raise CommandError("too_deep", ", ".join(sorted(chosen)))


def cmd_lock(w, cmd):
    viewer = w.users.viewer(cmd.arg(0))
    name = cmd.arg(1)
    roots = parse_roots(w, viewer, cmd.args[2:])
    chosen = solve(w, viewer, roots)
    entries = [(key, chosen[key].text) for key in sorted(chosen)]
    lock = Lock(name, viewer.name if viewer else "-", [r[0].key for r in roots], entries, w.now)
    w.locks[name] = lock
    w.emit("lock %s (%d packages)" % (name, len(entries)))
    for key, ver in entries:
        w.emit("  %s %s" % (w.registry.packages[key].name, ver))
    w.emit("digest %s" % lock.digest)


def cmd_outdated(w, cmd):
    viewer = w.users.viewer(cmd.arg(0))
    lock = w.locks.get(cmd.arg(1))
    if lock is None:
        raise CommandError("unknown_lock", cmd.arg(1))
    rows = []
    for key, ver in lock.entries:
        pkg = w.registry.packages.get(key)
        if pkg is None or not perms.can(w, viewer, pkg, "read"):
            rows.append("  %s %s -> gone" % (key, ver))
            continue
        latest = pkg.tags.get("latest")
        rel = pkg.releases.get(ver)
        if rel is None:
            rows.append("  %s %s -> unpublished (latest %s)" % (pkg.name, ver, latest or "-"))
        elif rel.yanked:
            rows.append("  %s %s -> yanked (latest %s)" % (pkg.name, ver, latest or "-"))
        elif latest is not None and latest != ver:
            rows.append("  %s %s -> %s" % (pkg.name, ver, latest))
    w.emit("outdated %s: %d of %d" % (lock.name, len(rows), len(lock.entries)))
    for row in rows:
        w.emit(row)
