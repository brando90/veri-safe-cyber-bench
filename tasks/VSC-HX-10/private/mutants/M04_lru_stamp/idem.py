# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The idempotency cache.

Maps an idempotency key to the packed transaction id of the operation that
first used it.  Bounded to ``capacity`` entries; recency is kept with use
stamps in a heap.
"""
import heapq


class Entry:
    __slots__ = ("packed", "stamp")

    def __init__(self, packed, stamp):
        self.packed = packed
        self.stamp = stamp


class IdemCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.entries = {}
        self.heap = []
        self.clock = 0
        self.evicted = 0

    def __len__(self):
        return len(self.entries)

    def _tick(self):
        self.clock += 1
        return self.clock

    def lookup(self, key):
        entry = self.entries.get(key)
        if entry is None:
            return None
        entry.stamp = self._tick()
        heapq.heappush(self.heap, (entry.stamp, key))
        self._tidy()
        return entry.packed

    def store(self, key, packed):
        entry = Entry(packed, self._tick())
        self.entries[key] = entry
        heapq.heappush(self.heap, (entry.stamp, key))
        while len(self.entries) > self.capacity:
            self._evict_one()
        self._tidy()

    def _evict_one(self):
        while self.heap:
            stamp, key = heapq.heappop(self.heap)
            entry = self.entries.get(key)
            if entry is not None:
                del self.entries[key]
                self.evicted += 1
                return

    def _tidy(self):
        if len(self.heap) > 4 * self.capacity:
            self.heap = [(e.stamp, k) for k, e in self.entries.items()]
            heapq.heapify(self.heap)
