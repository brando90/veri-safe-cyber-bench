# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Parsing and printing of instants, durations, offsets and clock times.

The logical clock starts at ``d0 00:00:00.000`` (day 0, UTC) and counts
milliseconds.  An instant is printed ``dN HH:MM:SS.mmm`` in UTC.

Syntax accepted on input (README, "Time"):

* duration: ``<digits><unit>`` with unit ``ms``, ``s``, ``m``, ``h`` or ``d``;
* instant: ``dN`` followed by ``HH:MM``, ``HH:MM:SS`` or ``HH:MM:SS.mmm``;
* UTC offset: ``+HH:MM`` or ``-HH:MM``, at most 14:00 either way;
* clock time of day: ``HH:MM`` (00:00 .. 23:59).
"""

import re

import units
from errors import CommandError

_DUR_RE = re.compile(r"^([0-9]{1,9})(ms|s|m|h|d)$")
_DUR_SCALE = {
    "ms": 1,
    "s": units.MS_PER_S,
    "m": units.MS_PER_MIN,
    "h": units.MS_PER_HOUR,
    "d": units.MS_PER_DAY,
}
_DAY_RE = re.compile(r"^d([0-9]{1,5})$")
_CLOCK_RE = re.compile(r"^([0-9]{2}):([0-9]{2})(?::([0-9]{2})(?:\.([0-9]{3}))?)?$")
_OFFSET_RE = re.compile(r"^([+-])([0-9]{2}):([0-9]{2})$")
_HHMM_RE = re.compile(r"^([0-9]{2}):([0-9]{2})$")

MAX_OFFSET_MIN = 14 * units.MIN_PER_HOUR


def parse_duration(tok):
    """'90s' -> 90000.  Returns milliseconds."""
    m = _DUR_RE.match(tok)
    if not m:
        raise CommandError("bad duration " + tok)
    return int(m.group(1)) * _DUR_SCALE[m.group(2)]


def parse_instant(day_tok, clock_tok):
    """('d1', '09:30') -> milliseconds since d0 00:00 UTC."""
    m = _DAY_RE.match(day_tok)
    c = _CLOCK_RE.match(clock_tok)
    if not m or not c:
        raise CommandError("bad instant %s %s" % (day_tok, clock_tok))
    hh, mm = int(c.group(1)), int(c.group(2))
    ss = int(c.group(3) or 0)
    ms = int(c.group(4) or 0)
    if hh > 23 or mm > 59 or ss > 59:
        raise CommandError("bad instant %s %s" % (day_tok, clock_tok))
    return (int(m.group(1)) * units.MS_PER_DAY + hh * units.MS_PER_HOUR
            + mm * units.MS_PER_MIN + ss * units.MS_PER_S + ms)


def parse_offset(tok):
    """'+05:30' -> 330, '-08:00' -> -480 (minutes east of UTC)."""
    m = _OFFSET_RE.match(tok)
    if not m:
        raise CommandError("bad offset " + tok)
    hh, mm = int(m.group(2)), int(m.group(3))
    if mm > 59:
        raise CommandError("bad offset " + tok)
    total = hh * units.MIN_PER_HOUR + mm
    if total > MAX_OFFSET_MIN:
        raise CommandError("bad offset " + tok)
    return -total if m.group(1) == "-" else total


def parse_hhmm(tok):
    """'22:00' -> 1320 (minute of the day)."""
    m = _HHMM_RE.match(tok)
    if not m:
        raise CommandError("bad time of day " + tok)
    hh, mm = int(m.group(1)), int(m.group(2))
    if hh > 23 or mm > 59:
        raise CommandError("bad time of day " + tok)
    return hh * units.MIN_PER_HOUR + mm


def fmt_instant(ms):
    day, rest = divmod(ms, units.MS_PER_DAY)
    hh, rest = divmod(rest, units.MS_PER_HOUR)
    mm, rest = divmod(rest, units.MS_PER_MIN)
    ss, milli = divmod(rest, units.MS_PER_S)
    return "d%d %02d:%02d:%02d.%03d" % (day, hh, mm, ss, milli)


def fmt_offset(minutes):
    sign = "-" if minutes < 0 else "+"
    hh, mm = divmod(abs(minutes), units.MIN_PER_HOUR)
    return "%s%02d:%02d" % (sign, hh, mm)


def fmt_hhmm(minute_of_day):
    hh, mm = divmod(minute_of_day, units.MIN_PER_HOUR)
    return "%02d:%02d" % (hh, mm)


def fmt_seconds(ms):
    """Durations in listings: whole seconds when exact, else milliseconds."""
    if ms % units.MS_PER_S == 0:
        return "%ds" % (ms // units.MS_PER_S)
    return "%dms" % ms
