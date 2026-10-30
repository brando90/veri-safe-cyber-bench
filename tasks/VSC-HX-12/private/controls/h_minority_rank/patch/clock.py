# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The logical clock (whole seconds, starts at 0) and the clock command."""
import timeutil
from errors import CommandError


class Clock:
    def __init__(self):
        self.now = 0

    def set(self, t):
        if t < self.now:
            raise CommandError("clock_back", self.now)
        self.now = t

    def advance(self, d):
        self.now += d


def cmd_set(w, cmd):
    w.clock.set(timeutil.parse_instant(cmd.arg(0)))
    w.emit("clock %d" % w.now)


def cmd_advance(w, cmd):
    w.clock.advance(timeutil.parse_duration(cmd.arg(0)))
    w.emit("clock %d" % w.now)


def cmd_show(w, cmd):
    w.emit("clock %d" % w.now)
