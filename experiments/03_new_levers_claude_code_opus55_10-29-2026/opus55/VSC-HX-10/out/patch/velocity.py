# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Counting debits per whole minute over a ring of minute buckets."""
import units


class MinuteRing:
    __slots__ = ("size", "minutes", "counts")

    def __init__(self, size):
        self.size = size
        self.minutes = [-1] * size
        self.counts = [0] * size

    def note(self, now):
        m = units.minute_of(now)
        i = m % self.size
        if self.minutes[i] != m:
            self.minutes[i] = m
            self.counts[i] = 0
        self.counts[i] += 1

    def count(self, now):
        m = units.minute_of(now)
        total = 0
        for minute, n in zip(self.minutes, self.counts):
            if minute >= 0 and 0 <= m - minute < self.size:
                total += n
        return total
