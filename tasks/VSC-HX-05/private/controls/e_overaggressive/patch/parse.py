# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Line splitting and field validation.

Every validator either returns the converted value or raises CommandError
with the documented error text (README, "Errors").  The same validators are
used by the interactive commands and by `import`, so a value is accepted or
rejected the same way whichever way it arrives.
"""

import datetime
import re

import money
from errors import CommandError

TOKEN = re.compile(r"[^ \t]+")
BLANKS = " \t"

NAME_RE = re.compile(r"[a-z][a-z0-9_.-]{0,15}\Z")
PHONE_RE = re.compile(r"[0-9+()-]{3,20}\Z")
EMAIL_RE = re.compile(r"[^@ \t]+@[^@ \t]+\Z")
CODE_RE = re.compile(r"[A-Z][A-Z0-9]{1,7}\Z")
DAY_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
TIME_RE = re.compile(r"(\d{2}):(\d{2})\Z")
COUNT_RE = re.compile(r"\d{1,6}\Z")

OPEN_MIN = 8 * 60
CLOSE_MIN = 18 * 60
TEXT_LIMITS = {"name": 80, "note": 200, "reason": 200, "text": 80}
METHODS = ("cash", "card", "transfer")
STATUSES = ("done", "noshow", "cancelled")


def tokens(line):
    return TOKEN.findall(line)


def take(line, n):
    """Split N tokens off LINE.

    Returns (tokens, rest): REST is the remainder of the line with blanks
    (space, TAB) trimmed at both ends.  If LINE has fewer than N tokens,
    returns (tokens, None).
    """
    rest = line.strip(BLANKS)
    toks = []
    for _ in range(n):
        m = TOKEN.match(rest)
        if not m:
            return toks, None
        toks.append(m.group(0))
        rest = rest[m.end():].lstrip(BLANKS)
    return toks, rest


def usage(text):
    return CommandError("usage: " + text)


def user_name(s):
    if not NAME_RE.match(s) or s == "nobody":
        raise CommandError("bad-name: " + s)
    return s


def role_name(s):
    if not NAME_RE.match(s) or s == "nobody":
        raise CommandError("bad-name: " + s)
    return s


def obj_id(prefix, s):
    m = re.match(prefix + r"(\d{1,6})\Z", s)
    if not m or int(m.group(1)) == 0:
        raise CommandError("bad-id: " + s)
    return int(m.group(1))


def fmt_id(prefix, n):
    return "%s%04d" % (prefix, n)


def phone(s):
    if not PHONE_RE.match(s):
        raise CommandError("bad-phone: " + s)
    return s


def email(s):
    if s != "-" and not EMAIL_RE.match(s):
        raise CommandError("bad-email: " + s)
    return s


def text(s, field, allow_empty=False, allow_tab=False):
    """Free text (names, notes, reasons): stored exactly as given."""
    if s == "" and not allow_empty:
        raise CommandError("empty: " + field)
    if len(s) > TEXT_LIMITS[field]:
        raise CommandError("too-long: " + field)
    bad = "\r\n\"\\" if allow_tab else "\t\r\n\"\\"
    if any(c in bad for c in s):
        raise CommandError("bad-text: " + field)
    return s


def code(s):
    if not CODE_RE.match(s):
        raise CommandError("bad-code: " + s)
    return s


def minutes(s):
    if not COUNT_RE.match(s) or not 5 <= int(s) <= 480 or int(s) % 5:
        raise CommandError("bad-minutes: " + s)
    return int(s)


def amount(s):
    cents = money.parse_cents(s)
    if cents is None:
        raise CommandError("bad-money: " + s)
    return cents


def rate(s):
    bp = money.parse_rate(s)
    if bp is None:
        raise CommandError("bad-rate: " + s)
    return bp


def day(s):
    if not DAY_RE.match(s):
        raise CommandError("bad-day: " + s)
    try:
        datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
    except ValueError:
        raise CommandError("bad-day: " + s) from None
    return s


def time_of_day(s):
    """'09:30' -> 570 (minutes after midnight); 5-minute grid only."""
    m = TIME_RE.match(s)
    if not m:
        raise CommandError("bad-time: " + s)
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59 or mi % 5:
        raise CommandError("bad-time: " + s)
    return h * 60 + mi


def fmt_time(minute_of_day):
    return "%02d:%02d" % divmod(minute_of_day, 60)


def percent(s):
    if not COUNT_RE.match(s) or int(s) > 100:
        raise CommandError("bad-percent: " + s)
    return int(s)


def method(s):
    if s not in METHODS:
        raise CommandError("bad-method: " + s)
    return s


def status(s):
    if s not in STATUSES:
        raise CommandError("bad-status: " + s)
    return s


def count(s):
    if not COUNT_RE.match(s) or int(s) == 0:
        raise CommandError("bad-count: " + s)
    return int(s)
