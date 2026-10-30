# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Logical clock and duration helpers.

Time is a whole number of seconds since the start of the run (0).  It only
moves when a `clock` command moves it, which keeps every run deterministic.
"""
import re

from errors import ClockError, UsageError

UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
_DURATION_RE = re.compile(r"(\d{1,9})([smhd]?)")
_INT_RE = re.compile(r"\d{1,12}")


class Clock:
    def __init__(self):
        self.now = 0

    def set(self, t):
        if t < self.now:
            raise ClockError("clock cannot go backwards (now %d)" % self.now)
        self.now = t

    def advance(self, seconds):
        self.now += seconds


def parse_int(text, what):
    if not _INT_RE.fullmatch(text):
        raise UsageError("bad %s %s" % (what, text))
    return int(text)


def parse_duration(text):
    """'90' or '90s', '5m', '2h', '1d' -> seconds.  A bare number is seconds."""
    m = _DURATION_RE.fullmatch(text)
    if not m:
        raise UsageError("bad duration %s" % text)
    seconds = int(m.group(1)) * UNITS[m.group(2) or "s"]
    if seconds <= 0:
        raise UsageError("duration must be positive")
    return seconds


def expired(deadline, now):
    """True once NOW has reached DEADLINE (validity is [start, deadline))."""
    return now >= deadline


def remaining(deadline, now):
    """Seconds left before DEADLINE (0 once expired)."""
    return max(0, deadline - now)
