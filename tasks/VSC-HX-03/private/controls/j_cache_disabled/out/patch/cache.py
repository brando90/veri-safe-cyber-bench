# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The render cache used by BUILD.

A cache entry holds the rendered text of one page together with the files
that were read to produce it (its dependencies) and their digests. An entry
is reused only while every dependency still has the same content, so editing
a partial or an asset invalidates every page that used it.

Entries live in memory for the rest of the run; a copy of the rendered text
is also written to ``cache/<digest of page and text>.html`` so CLEAN and LS
can see it.
"""

import hashlib
import os


def digest(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class Deps:
    """Files read while rendering one page: real path -> digest (first read wins)."""

    def __init__(self):
        self.files = {}

    def record(self, real, data):
        self.files.setdefault(real, digest(data))


class Entry:
    def __init__(self, owner, output, deps):
        self.owner = owner
        self.output = output
        self.deps = dict(deps.files)


def make_key(tenant, page_rel, source):
    """Key for one page: what it is, what it says and the settings it sees."""
    h = hashlib.sha256()
    session = "\n".join("%s=%s" % item for item in sorted(tenant.session_vars.items()))
    # built-in variables are fixed for a tenant, so they are not part of the key
    for part in (tenant.root, page_rel, source, tenant.config.fingerprint(), session):
        h.update(part.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


class RenderCache:
    def __init__(self):
        self._entries = {}
        self._stats = {}

    def _counters(self, tenant):
        return self._stats.setdefault(tenant.root, [0, 0])

    def lookup(self, tenant, key):
        """Rendered text for ``key`` if the entry is still valid, else None."""
        entry = None
        if entry is None:
            return None
        for path, expected in entry.deps.items():
            if not os.path.isfile(path):
                return None
            if digest(tenant.guard.read_bytes(path)) != expected:
                return None
        return entry.output

    def plan_files(self, tenant, fresh):
        """Checked locations of the cache files for freshly rendered pages."""
        planned = []
        for _key, page_rel, output, _deps in fresh:
            name = digest(page_rel + "\0" + output)[:16] + ".html"
            dest = tenant.locate_for_write(tenant.cache_dir, tenant.cache_dir, name)
            planned.append((dest, output.encode("utf-8")))
        return planned

    def commit(self, tenant, fresh, planned, hits, misses):
        """Store freshly rendered pages after a successful BUILD and count."""
        counters = self._counters(tenant)
        counters[0] += hits
        counters[1] += misses
        for key, _page_rel, output, deps in fresh:
            self._entries[key] = Entry(tenant.root, output, deps)
        for dest, data in planned:
            tenant.guard.write_bytes(dest, data)

    def forget(self, tenant):
        for key in [k for k, e in self._entries.items() if e.owner == tenant.root]:
            del self._entries[key]

    def stats(self, tenant):
        hits, misses = self._counters(tenant)
        entries = sum(1 for e in self._entries.values() if e.owner == tenant.root)
        return hits, misses, entries
