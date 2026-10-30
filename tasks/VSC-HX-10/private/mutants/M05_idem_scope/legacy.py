# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Version 1 helpers, kept for the old export tooling.  Not used by main.py."""


def lowest_free_slot(busy):
    for i, used in enumerate(busy):
        if not used:
            return i
    return None


class FlatRecent:
    """Bounded recently-used list (v1 idempotency store)."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.items = []

    def get(self, key):
        for k, v in self.items:
            if k == key:
                return v
        return None

    def put(self, key, value):
        self.items.append((key, value))
        if len(self.items) > self.capacity:
            self.items.pop(0)


def money_v1(cents):
    return "%.2f" % (cents / 100.0)


def segment_of(index, size):
    return index // size
