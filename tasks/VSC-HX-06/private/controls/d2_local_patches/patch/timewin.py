# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Sliding time windows.

A window of width W that ends at NOW covers the instants E with
NOW - W < E <= NOW: something that happened exactly W ago has left the
window.  Duplicate detection and the rolling hourly limit both use this
module so that the edge is the same everywhere.
"""


def within(earlier, now, width_ms):
    """True if instant EARLIER (<= NOW) lies in the window of WIDTH_MS that
    ends at NOW."""
    return now - earlier <= width_ms


def leaves_at(earlier, width_ms):
    """First instant at which EARLIER is no longer in a window of WIDTH_MS."""
    return earlier + width_ms


class Rolling:
    """Instants of past events, oldest first, for one rolling window."""

    def __init__(self, width_ms):
        self.width_ms = width_ms
        self._times = []

    def add(self, t):
        self._times.append(t)

    def prune(self, now):
        keep = 0
        while keep < len(self._times) and not within(self._times[keep], now, self.width_ms):
            keep += 1
        if keep:
            del self._times[:keep]

    def count(self, now):
        self.prune(now)
        return sum(1 for t in self._times if t <= now)

    def wakeups(self, now):
        """Instants after NOW at which an event leaves the window."""
        return [leaves_at(t, self.width_ms) for t in self._times
                if leaves_at(t, self.width_ms) > now]
