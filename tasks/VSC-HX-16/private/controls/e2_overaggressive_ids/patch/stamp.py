# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Timestamps: parsing, UTC conversion, formatting and age arithmetic."""
import re
from datetime import datetime, timedelta, timezone

UTC = timezone.utc
STAMP_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(Z|[+-]\d{4})?$")
DAY = 86400


def parse(text):
    """Return an aware UTC datetime for TEXT, or None when it is not a stamp.

    A stamp without a zone is taken as UTC.  Local times are converted to UTC
    by subtracting the written offset.
    """
    m = STAMP_RE.match(text)
    if m is None:
        return None
    y, mo, d, h, mi, s = (int(g) for g in m.groups()[:6])
    try:
        base = datetime(y, mo, d, h, mi, s, tzinfo=UTC)
    except ValueError:
        return None
    zone = m.group(7)
    if zone and zone != "Z":
        oh, om = int(zone[1:3]), int(zone[3:5])
        if oh > 23 or om > 59:
            return None
        delta = timedelta(hours=oh, minutes=om)
        base = base - delta if zone[0] == "+" else base + delta
    return base


def fmt(when):
    return when.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def seconds(when):
    return int(when.timestamp())


def older_than(now, when, days):
    """True when WHEN is more than DAYS days before NOW."""
    return now - when > timedelta(days=days)


def days_ahead(now, when):
    """Whole days WHEN lies after NOW, rounded up; 0 when it is not later."""
    ahead = seconds(when) - seconds(now)
    if ahead <= 0:
        return 0
    return ahead // DAY


def day_of(when):
    """The UTC calendar day of WHEN as YYYY-MM-DD."""
    return when.astimezone(UTC).date().isoformat()
