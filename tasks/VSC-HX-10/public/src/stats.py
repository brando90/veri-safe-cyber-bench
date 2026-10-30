# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Per-slot activity counters shown by ``accounts``."""


class UsageCounters:
    def __init__(self, size):
        self.ops = [0] * size
        self.last = [None] * size

    def note(self, slot, now):
        self.ops[slot] += 1
        self.last[slot] = now

    def ops_of(self, slot):
        return self.ops[slot]

    def clear_slot(self, idx):
        self.ops[idx] = 0
        self.last[idx] = None
