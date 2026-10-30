# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Recipient-local time: local day numbers, minute of the day, quiet hours.

A recipient has a fixed UTC offset in minutes (no daylight saving).  Local
time = UTC + offset.  Local days start at local midnight; the local day of
an instant can be -1 for a recipient west of UTC on the first hours of d0.
"""

import units


def local_ms(t, offset_min):
    return t + offset_min * units.MS_PER_MIN


def local_day(t, offset_min):
    """Local day number of instant T."""
    return local_ms(t, offset_min) // units.MS_PER_DAY


def minute_of_day(t, offset_min):
    """Local minute of the day (0..1439) of instant T."""
    return (local_ms(t, offset_min) // units.MS_PER_MIN) % units.MIN_PER_DAY


def next_local_midnight(t, offset_min):
    """UTC instant of the first local midnight strictly after T."""
    day = local_day(t, offset_min) + 1
    return day * units.MS_PER_DAY - offset_min * units.MS_PER_MIN


def in_window(minute, start, end):
    """True if MINUTE lies in [START, END), a window that may wrap past
    midnight (START > END means it runs over midnight)."""
    if start < end:
        return start <= minute < end
    return minute >= start or minute < end


def in_quiet(t, offset_min, window):
    """True if instant T falls in the recipient's quiet hours.  WINDOW is
    (start, end) in local minutes, or None for no quiet hours."""
    if window is None:
        return False
    start, end = window
    return in_window(minute_of_day(t, offset_min), start, end)


def next_minute(t):
    """First whole minute strictly after T (quiet hours and local days only
    change on whole minutes, since offsets are whole minutes)."""
    return (t // units.MS_PER_MIN + 1) * units.MS_PER_MIN
