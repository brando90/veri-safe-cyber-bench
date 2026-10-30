# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The response cache.

Only successful (200) GET responses of cacheable routes are stored, for the
``cache.ttl`` of the tenant (the default layer's value for shared routes);
a ttl of 0 turns caching off.  An entry stored at S with ttl D is served
while now < S + D.

Capacity: every entry is accounted at its size rounded up to whole KiB;
the cache holds at most ``cache.capacity`` rounded down to whole KiB.
When a new entry does not fit, least recently used entries are evicted
first; an entry bigger than the whole capacity is not stored.
"""
from collections import OrderedDict

import lexer
import timeutil
import units
from errors import CommandError


class Entry:
    __slots__ = ("key", "owner", "path", "status", "body", "nbytes", "size",
                 "stored_at", "expires_at", "hits")

    def __init__(self, key, owner, path, resp, stored_at, expires_at):
        self.key = key
        self.owner = owner
        self.path = path
        self.status = resp.status
        self.body = resp.body
        self.nbytes = resp.nbytes
        self.size = units.kib_ceil(resp.nbytes)   # accounted size, whole KiB
        self.stored_at = stored_at
        self.expires_at = expires_at
        self.hits = 0


class ResponseCache:
    def __init__(self, world):
        self.world = world
        self.entries = OrderedDict()
        self.used = 0          # whole KiB, sum of Entry.size
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def capacity(self):
        """The configured capacity."""
        return self.world.config.size_bytes(None, "cache.capacity")

    def _drop(self, key):
        entry = self.entries.pop(key)
        self.used -= entry.size
        return entry

    def get(self, key, now):
        entry = self.entries.get(key)
        if entry is not None and timeutil.expired(now, entry.expires_at):
            self._drop(key)
            entry = None
        if entry is None:
            self.misses += 1
            return None
        self.entries.move_to_end(key)
        entry.hits += 1
        self.hits += 1
        return entry

    def put(self, key, owner, path, resp, now, ttl):
        if ttl <= 0:
            return False
        if key in self.entries:
            self._drop(key)
        entry = Entry(key, owner, path, resp, now, timeutil.deadline_after(now, ttl))
        cap = self.capacity()
        if entry.size > cap:
            return False
        while self.entries and self.used + entry.size > cap:
            self._drop(next(iter(self.entries)))
            self.evictions += 1
        self.entries[key] = entry
        self.used += entry.size
        return True

    def purge(self, owner, path=None):
        doomed = [k for k, e in self.entries.items()
                  if e.owner == owner and (path is None or e.path == path)]
        for key in doomed:
            self._drop(key)
        return len(doomed)

    def expire(self, now):
        doomed = [k for k, e in self.entries.items() if timeutil.expired(now, e.expires_at)]
        for key in doomed:
            self._drop(key)
        return len(doomed)


def cmd_cache(world, cmd):
    if len(cmd.words) < 2:
        raise CommandError("usage: cache stats|list|purge ...")
    lexer.allow_opts(cmd, ())
    cache = world.cache
    sub = cmd.words[1]
    if sub == "stats":
        lexer.need(cmd, 2, 2, "cache stats")
        cache.expire(world.now)
        world.emit("cache entries=%d used=%dKiB capacity=%s hits=%d misses=%d evictions=%d" % (
            len(cache.entries), cache.used,
            units.fmt_size(world.config.size_bytes(None, "cache.capacity")),
            cache.hits, cache.misses, cache.evictions))
    elif sub == "list":
        lexer.need(cmd, 2, 2, "cache list")
        cache.expire(world.now)
        if not cache.entries:
            world.emit("cache empty")
        for entry in cache.entries.values():
            world.emit("entry %s size=%dKiB expires=%d hits=%d" % (
                entry.key, entry.size, entry.expires_at, entry.hits))
    elif sub == "purge":
        lexer.need(cmd, 3, 3, "cache purge TENANT")
        tenant = world.tenants.require(cmd.words[2]).name
        n = cache.purge(tenant)
        world.audit.record(tenant, "cache.purge", [("entries", n)])
        world.emit("cache purged %d entries of %s" % (n, tenant))
    else:
        raise CommandError("cache: unknown subcommand %s" % sub)
