# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Units used across quotagate: durations, sizes, integers and money.

Conventions (see README.md, "Units"):

* every duration inside the program is an integer number of milliseconds;
  on input a duration is NUMBER with an optional unit ms, s, m, h or d and a
  bare NUMBER means milliseconds;
* every size inside the program is an integer number of bytes; on input a
  size is NUMBER with an optional unit B, KiB or MiB (1 KiB = 1024 bytes)
  and a bare NUMBER means bytes;
* money is kept in integer millicents (1 cent = 1000 millicents) and only
  turned into cents when a bill line is printed.
"""
import re

from errors import CommandError

MS = 1
SECOND = 1000
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR

KIB = 1024
MIB = 1024 * KIB

MILLICENTS_PER_CENT = 1000

_DURATION_UNITS = {"ms": MS, "s": SECOND, "m": MINUTE, "h": HOUR, "d": DAY}
_DURATION_ORDER = (("d", DAY), ("h", HOUR), ("m", MINUTE), ("s", SECOND))
_SIZE_UNITS = {"B": 1, "KiB": KIB, "MiB": MIB}

_DURATION_RE = re.compile(r"(\d{1,12})(ms|s|m|h|d)?")
_SIZE_RE = re.compile(r"(\d{1,12})(B|KiB|MiB)?")
_INT_RE = re.compile(r"-?\d{1,15}")


def parse_duration(text, what="duration"):
    """Parse a duration and return milliseconds."""
    m = _DURATION_RE.fullmatch(text)
    if m is None:
        raise CommandError("bad %s %s (expected NUMBER[ms|s|m|h|d])" % (what, text))
    return int(m.group(1)) * _DURATION_UNITS[m.group(2) or "ms"]


def fmt_duration(ms):
    """Canonical text of a duration: the largest unit that divides it exactly."""
    if ms == 0:
        return "0s"
    for unit, size in _DURATION_ORDER:
        if ms % size == 0:
            return "%d%s" % (ms // size, unit)
    return "%dms" % ms


def parse_size(text, what="size"):
    """Parse a size and return bytes."""
    m = _SIZE_RE.fullmatch(text)
    if m is None:
        raise CommandError("bad %s %s (expected NUMBER[B|KiB|MiB])" % (what, text))
    return int(m.group(1)) * _SIZE_UNITS[m.group(2) or "B"]


def fmt_size(nbytes):
    """Canonical text of a size: MiB or KiB when exact, else bytes."""
    if nbytes and nbytes % MIB == 0:
        return "%dMiB" % (nbytes // MIB)
    if nbytes and nbytes % KIB == 0:
        return "%dKiB" % (nbytes // KIB)
    return "%dB" % nbytes


def parse_int(text, what, lo=None, hi=None):
    """Parse a decimal integer and check it against [lo, hi]."""
    if _INT_RE.fullmatch(text) is None:
        raise CommandError("bad %s %s (expected an integer)" % (what, text))
    value = int(text)
    if lo is not None and value < lo:
        raise CommandError("%s must be at least %d" % (what, lo))
    if hi is not None and value > hi:
        raise CommandError("%s must be at most %d" % (what, hi))
    return value


def parse_flag(text, what):
    if text in ("on", "off"):
        return text == "on"
    raise CommandError("bad %s %s (expected on or off)" % (what, text))


def ceil_div(num, den):
    """Integer division rounding up, for non-negative NUM and positive DEN."""
    return -(-num // den)


def kib_ceil(nbytes):
    """Whole KiB needed to hold NBYTES (a 1-byte payload needs 1 KiB)."""
    return ceil_div(nbytes, KIB)


def kib_floor(nbytes):
    """Whole KiB contained in NBYTES (used for capacities: never round a limit up)."""
    return nbytes // KIB


def round_half_up(num, den):
    """NUM/DEN rounded to the nearest integer, halves away from zero (NUM >= 0)."""
    return (2 * num + den) // (2 * den)


def ms_to_whole_seconds(ms):
    """Seconds to wait, rounded up, never less than one (``retry_after``)."""
    return max(1, ceil_div(ms, SECOND))


def millicents_to_cents(mc):
    """Bill lines are rounded half up to whole cents."""
    return ceil_div(mc, MILLICENTS_PER_CENT)


def fmt_money(cents):
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "%s%d.%02d" % (sign, cents // 100, cents % 100)
