# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The logical clock (integer milliseconds, starts at 0)."""
from errors import CommandError


class Clock:
    def __init__(self):
        self.now = 0

    def target(self, when):
        if when < self.now:
            raise CommandError("clock cannot move backwards")
        return when

    def target_after(self, duration):
        return self.now + duration

    def move(self, when):
        self.now = when
