# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""UTC offsets: text to minutes east of UTC and back."""
import re

from errors import CommandError

OFFSET_RE = re.compile(r"([+-])(\d{2})(?::?(\d{2}))?")
MIN_OFFSET = -12 * 60
MAX_OFFSET = 14 * 60


def parse(text):
    if text in ("Z", "z"):
        return 0
    m = OFFSET_RE.fullmatch(text)
    if m is None:
        raise CommandError("bad_offset", text)
    minutes = int(m.group(2)) * 60 + int(m.group(3) or 0)
    if int(m.group(3) or 0) > 59:
        raise CommandError("bad_offset", text)
    if m.group(1) == "-":
        minutes = -minutes
    if not MIN_OFFSET <= minutes <= MAX_OFFSET:
        raise CommandError("bad_offset", text)
    return minutes


def fmt(minutes):
    if minutes == 0:
        return "Z"
    hours = int(minutes / 60)
    mins = abs(minutes) - abs(hours) * 60
    sign = "-" if minutes < 0 else "+"
    return "%s%02d:%02d" % (sign, abs(hours), mins)


def to_utc(local_secs, minutes):
    return local_secs - minutes * 60
