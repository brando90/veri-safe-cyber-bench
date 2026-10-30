# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""today and tick: the logical clock."""
import money
import timeutil


def cmd_today(w, cmd):
    w.out.emit("day %d period %d" % (w.day, timeutil.period_of(w.day)))


def cmd_tick(w, cmd):
    days = money.parse_int(cmd.arg(0), 1, timeutil.MAX_TICK)
    w.day += days
    w.out.emit("day %d period %d" % (w.day, timeutil.period_of(w.day)))
