# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Durations, instants and deadlines on the logical clock."""
import re

from errors import CommandError

_UNITS = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}
_DUR_RE = re.compile(r"(\d{1,9})(s|m|h|d)?")


def parse_duration(text):
    m = _DUR_RE.fullmatch(text or "")
    if m is None:
        raise CommandError("bad_duration", text)
    return int(m.group(1)) * _UNITS[m.group(2) or ""]


def parse_instant(text):
    return parse_duration(text)


def fmt_duration(sec):
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60)):
        if sec and sec % size == 0:
            return "%d%s" % (sec // size, unit)
    return "%ds" % sec


def deadline_after(now, duration):
    if duration is None:
        return None
    return now + duration


def expired(now, deadline):
    if deadline is None:
        return False
    return now >= deadline


def fmt_deadline(deadline):
    return "never" if deadline is None else str(deadline)
