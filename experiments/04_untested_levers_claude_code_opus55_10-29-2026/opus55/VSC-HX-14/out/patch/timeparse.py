# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Dates, times of day and start instants as typed in commands.

A local instant is a count of seconds since 1970-01-01T00:00 local time.
Stored starts have minute resolution; a start given with seconds is moved
to the nearest minute (half a minute rounds up).
"""
import re

import civil
from errors import CommandError

DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
START_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?")


def parse_date(text):
    m = DATE_RE.fullmatch(text)
    if m is None:
        raise CommandError("bad_date", text)
    y, mo, d = (int(g) for g in m.groups())
    if not civil.valid(y, mo, d):
        raise CommandError("bad_date", text)
    return civil.days_from_civil(y, mo, d)


def format_date(z):
    y, m, d = civil.civil_from_days(z)
    return "%04d-%02d-%02d" % (y, m, d)


def snap(secs):
    """SECS moved to the nearest minute (half a minute rounds up); the move
    carries into the hour, day, month and year as needed."""
    return (secs + 30) // 60 * 60


def parse_start(text, allday):
    """(start, raw) local instants for TEXT."""
    if allday:
        day = parse_date(text) if DATE_RE.fullmatch(text) else None
        if day is None:
            raise CommandError("bad_start", text)
        return day * 86400, day * 86400
    m = START_RE.fullmatch(text)
    if m is None:
        raise CommandError("bad_start", text)
    y, mo, d, h, mi = (int(g) for g in m.groups()[:5])
    s = int(m.group(6) or 0)
    if not civil.valid(y, mo, d) or h > 23 or mi > 59 or s > 59:
        raise CommandError("bad_start", text)
    raw = civil.days_from_civil(y, mo, d) * 86400 + h * 3600 + mi * 60 + s
    start = snap(raw)
    if not civil.in_range(start // 86400):
        raise CommandError("out_of_range")
    return start, raw


def split_instant(secs):
    day, sod = divmod(secs, 86400)
    return day, sod // 3600, sod % 3600 // 60, sod % 60


def format_instant(secs):
    day, h, mi, _ = split_instant(secs)
    return "%sT%02d:%02d" % (format_date(day), h, mi)


def format_exact(secs):
    day, h, mi, s = split_instant(secs)
    return "%sT%02d:%02d:%02d" % (format_date(day), h, mi, s)


def format_clock(sod):
    return "%02d:%02d" % (sod // 3600, sod % 3600 // 60)


def parse_instant(text):
    """Exact inverse of format_instant (no snapping)."""
    date, sep, clock = text.partition("T")
    h, colon, mi = clock.partition(":")
    if not sep or not colon or not (h + mi).isdecimal() or len(h) != 2 or len(mi) != 2:
        raise CommandError("bad_start", text)
    if int(h) > 23 or int(mi) > 59:
        raise CommandError("bad_start", text)
    return parse_date(date) * 86400 + int(h) * 3600 + int(mi) * 60
