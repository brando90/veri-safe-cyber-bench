# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Number parsing and formatting shared by every module."""
import re

from errors import CmdError

SEC_MS = 1000
MIN_MS = 60_000
HOUR_MS = 3_600_000
DAY_MS = 86_400_000

TEMP_RE = re.compile(r"^([+-]?)(\d{1,3})(?:\.(\d))?$")
SECONDS_RE = re.compile(r"^(\d{1,9})(?:\.(\d{1,3}))?$")
INT_RE = re.compile(r"^[+-]?\d{1,9}$")


def parse_tenths(text, lo=None, hi=None):
    m = TEMP_RE.match(text)
    if not m:
        raise CmdError("bad temperature %s" % text)
    value = int(m.group(2)) * 10 + int(m.group(3) or 0)
    if m.group(1) == "-":
        value = -value
    if lo is not None and value < lo:
        value = lo
    if hi is not None and value > hi:
        value = hi
    return value


def fmt_tenths(value):
    sign = "-" if value < 0 else ""
    mag = abs(value)
    return "%s%d.%d" % (sign, mag // 10, mag % 10)


def parse_ms(text):
    m = SECONDS_RE.match(text)
    if not m:
        raise CmdError("bad time %s" % text)
    frac = (m.group(2) or "").ljust(3, "0")
    return int(m.group(1)) * SEC_MS + int(frac)


def fmt_ms(ms):
    whole, rest = divmod(ms, SEC_MS)
    if rest == 0:
        return str(whole)
    return "%d.%s" % (whole, ("%03d" % rest).rstrip("0"))


def parse_int(text, name, lo, hi):
    if not INT_RE.match(text):
        raise CmdError("bad number for %s" % name)
    value = int(text)
    if value < lo or value > hi:
        raise CmdError("%s out of range" % name)
    return value


def div_round_half_up(num, den):
    return (2 * num + den) // (2 * den)


def day_clock(ms):
    day, rest = divmod(ms, DAY_MS)
    hours, rest = divmod(rest, HOUR_MS)
    minutes, rest = divmod(rest, MIN_MS)
    seconds, milli = divmod(rest, SEC_MS)
    text = "d%d %02d:%02d:%02d" % (day + 1, hours, minutes, seconds)
    if milli:
        text += ".%03d" % milli
    return text


def parse_clock(text):
    """Inverse of day_clock for whole-second texts such as 'd2 03:04:05'."""
    parts = text.split(" ")
    if len(parts) != 2 or not parts[0].startswith("d"):
        return None
    hms = parts[1].split(":")
    if len(hms) != 3 or not (parts[0][1:] + "".join(hms)).isdigit():
        return None
    day, h, m, s = int(parts[0][1:]), int(hms[0]), int(hms[1]), int(hms[2])
    if day < 1 or h > 23 or m > 59 or s > 59:
        return None
    return ((day - 1) * 86400 + h * 3600 + m * 60 + s) * SEC_MS
