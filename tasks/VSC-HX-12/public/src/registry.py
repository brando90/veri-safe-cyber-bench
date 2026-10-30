# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Packages, releases and the package table."""
import names
import semver
import units
from errors import CommandError


class Dependency:
    __slots__ = ("name", "key", "req")

    def __init__(self, name, req):
        self.name = name
        self.key = names.canonical(name)
        self.req = req

    def __str__(self):
        return "%s@%s" % (self.name, self.req.text)


class Release:
    __slots__ = ("ver", "text", "size", "deps", "publisher", "published_at",
                 "embargo_until", "yanked", "yank_reason", "deprecated", "downloads")

    def __init__(self, ver, size, deps, publisher, published_at, embargo_until):
        self.ver = ver
        self.text = ver.text
        self.size = size
        self.deps = deps
        self.publisher = publisher
        self.published_at = published_at
        self.embargo_until = embargo_until
        self.yanked = False
        self.yank_reason = ""
        self.deprecated = None
        self.downloads = 0

    @property
    def kib(self):
        return units.kib_ceil(self.size)


class Invite:
    __slots__ = ("target", "role", "invited_by", "expires_at")

    def __init__(self, target, role, invited_by, expires_at):
        self.target = target
        self.role = role
        self.invited_by = invited_by
        self.expires_at = expires_at


class Package:
    def __init__(self, name, created_at, visibility):
        self.name = name
        self.key = names.canonical(name)
        self.created_at = created_at
        self.visibility = visibility
        self.roles = {}
        self.releases = {}
        self.tags = {}
        self.burned = set()
        self.invites = {}
        self.downloads = 0

    def release(self, text):
        rel = self.releases.get(text)
        if rel is None:
            raise CommandError("unknown_version", self.name, text)
        return rel

    def sorted_releases(self):
        return sorted(self.releases.values(), key=lambda r: semver.key(r.ver))

    def recompute_latest(self):
        best = None
        for rel in self.sorted_releases():
            if rel.yanked or rel.ver.pre:
                continue
            best = rel
        if best is None:
            self.tags.pop("latest", None)
        else:
            self.tags["latest"] = best.text

    def drop_release(self, text):
        del self.releases[text]
        gone = sorted(t for t, v in self.tags.items() if v == text)
        for t in gone:
            del self.tags[t]
        self.recompute_latest()
        return gone

    def total_kib(self):
        return sum(rel.kib for rel in self.releases.values())

    def depends_on(self, key):
        for rel in self.releases.values():
            for dep in rel.deps:
                if dep.key == key:
                    return True
        return False

    def members(self):
        def order(item):
            user, role = item
            return (-LEVEL_ORDER[role], user)
        return sorted(self.roles.items(), key=order)


LEVEL_ORDER = {"reader": 1, "maintainer": 2, "owner": 3}


class Registry:
    def __init__(self, world):
        self.world = world
        self.packages = {}

    def lookup(self, name):
        return self.packages.get(names.canonical(name))

    def find(self, name):
        pkg = self.lookup(name)
        if pkg is None:
            raise CommandError("unknown_package", name)
        return pkg

    def create(self, name, owner, now, visibility):
        pkg = Package(name, now, visibility)
        pkg.roles[owner] = "owner"
        self.packages[pkg.key] = pkg
        return pkg

    def delete(self, pkg):
        del self.packages[pkg.key]

    def sorted(self):
        return [self.packages[k] for k in sorted(self.packages)]
