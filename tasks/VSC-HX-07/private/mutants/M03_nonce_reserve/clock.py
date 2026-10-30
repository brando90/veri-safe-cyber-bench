# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The injectable logical clock.

quotagate never reads the wall clock.  Time starts at 0 ms and only moves
when a ``clock set`` or ``clock advance`` command says so; it never moves
backwards and it never moves while a command is being processed.
"""
import lexer
import units
from errors import CommandError


class Clock:
    def __init__(self):
        self.now = 0

    def now_s(self):
        """Current time in whole seconds (truncated); for display only."""
        return self.now // units.SECOND

    def set(self, t):
        if t < self.now:
            raise CommandError("clock: cannot move back from %d to %d" % (self.now, t))
        self.now = t

    def advance(self, duration):
        self.now += duration


def cmd_clock(world, cmd):
    words = cmd.words
    lexer.allow_opts(cmd, ())
    if len(words) == 1:
        world.emit("now=%d" % world.clock.now)
        return
    sub = words[1]
    if sub == "set":
        lexer.need(cmd, 3, 3, "clock set TIME")
        world.clock.set(units.parse_duration(words[2], "time"))
    elif sub == "advance":
        lexer.need(cmd, 3, 3, "clock advance DURATION")
        world.clock.advance(units.parse_duration(words[2]))
    else:
        raise CommandError("clock: unknown subcommand %s" % sub)
    world.emit("now=%d" % world.clock.now)
