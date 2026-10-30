# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Small time helpers on the logical millisecond clock.

Every module that has to decide whether something is still valid, or which
window a moment belongs to, goes through these helpers so that the whole
program agrees on one convention (README.md, "Time").
"""


def deadline_after(now, duration):
    """The deadline of something that starts at NOW and lasts DURATION ms."""
    return now + duration


def expired(now, deadline):
    """True once NOW has reached DEADLINE (deadlines are exclusive).  A
    deadline of None never passes."""
    if deadline is None:
        return False
    return now >= deadline


def remaining(now, deadline):
    """Milliseconds left before DEADLINE (0 once it has passed)."""
    if deadline is None:
        return None
    return max(0, deadline - now)


def window_index(now, width):
    """Index of the fixed window of WIDTH ms that contains NOW."""
    return now // width


def window_start(now, width):
    return now - now % width


def window_end(now, width):
    """First millisecond after the fixed window that contains NOW."""
    return window_start(now, width) + width


def in_sliding(t, now, width):
    """Whether moment T lies in the sliding window (NOW - WIDTH, NOW]."""
    return now - width < t <= now


def in_fixed(t, now, width):
    """Whether moment T lies in the fixed window that contains NOW (T <= NOW)."""
    return window_start(now, width) <= t <= now


def fmt_deadline(deadline):
    return "never" if deadline is None else str(deadline)
