# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""A timing wheel of one-second buckets for hold deadlines."""
import units


class Wheel:
    def __init__(self, size):
        self.size = size
        self.buckets = [dict() for _ in range(size)]
        self.where = {}
        self.cursor = 0

    def __len__(self):
        return len(self.where)

    def schedule(self, ident, deadline):
        b = units.second_of(deadline) % self.size
        self.buckets[b][ident] = deadline
        self.where[ident] = b

    def cancel(self, ident):
        b = self.where.pop(ident, None)
        if b is not None:
            del self.buckets[b][ident]

    def pending(self, ident):
        return ident in self.where

    def due(self, now):
        now_s = units.second_of(now)
        if now_s - self.cursor >= self.size:
            first = now_s - self.size + 1
        else:
            first = self.cursor
        out = []
        for s in range(first, now_s + 1):
            bucket = self.buckets[s % self.size]
            if not bucket:
                continue
            for ident, deadline in list(bucket.items()):
                out.append((deadline, ident))
                del bucket[ident]
                del self.where[ident]
        self.cursor = now_s
        out.sort()
        return out
