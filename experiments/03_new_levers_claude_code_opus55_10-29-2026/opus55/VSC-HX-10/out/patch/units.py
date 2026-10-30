# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Units, sizes and number formats shared by the ledgerkeep modules."""
import re

from errors import CommandError

SECOND = 1000
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR

SLOTS = 256
SEGMENT_RECORDS = 128
COMPACT_AFTER = 4
IDEM_CAPACITY = 64
HOLD_ID_MAX = 999
MAX_LIVE_HOLDS = 500
HOLD_TTL_MIN = SECOND
HOLD_TTL_MAX = DAY
WHEEL_SECONDS = 1024
RING_MINUTES = 60
BATCH_MAX = 100
SETTLE_ENTRIES = 16
MAX_ATTEMPTS = 4
RETRY_BASE = 30 * SECOND

DEFAULT_DAILY = 50000
DEFAULT_VELOCITY = 30
MAX_VELOCITY = 1000
MAX_MONEY = 10 ** 11

_DUR_RE = re.compile(r"(\d{1,12})(ms|s|m|h|d)?")
_FACTOR = {None: 1, "ms": 1, "s": SECOND, "m": MINUTE, "h": HOUR, "d": DAY}
_MONEY_RE = re.compile(r"(\d{1,10})(?:\.(\d{1,2}))?")
_COUNT_RE = re.compile(r"\d{1,9}")


def parse_duration(text, what="duration"):
    m = _DUR_RE.fullmatch(text or "")
    if m is None:
        raise CommandError("bad %s %s" % (what, text))
    return int(m.group(1)) * _FACTOR[m.group(2)]


def parse_money(text, what="amount"):
    """Money in cents: ``12``, ``12.5`` and ``12.50`` are all accepted."""
    m = _MONEY_RE.fullmatch(text or "")
    if m is None:
        raise CommandError("bad %s %s" % (what, text))
    cents = int(m.group(1)) * 100
    frac = m.group(2)
    if frac:
        cents += int(frac.ljust(2, "0"))
    if cents > MAX_MONEY:
        raise CommandError("%s too large" % what)
    return cents


def parse_positive_money(text, what="amount"):
    cents = parse_money(text, what)
    if cents <= 0:
        raise CommandError("%s must be positive" % what)
    return cents


def parse_count(text, what, low, high):
    if text is None or _COUNT_RE.fullmatch(text) is None:
        raise CommandError("bad %s %s" % (what, text))
    value = int(text)
    if value < low or value > high:
        raise CommandError("%s out of range" % what)
    return value


def fmt_money(cents):
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return "%s%d.%02d" % (sign, cents // 100, cents % 100)


def day_of(ms):
    return ms // DAY


def minute_of(ms):
    return ms // MINUTE


def second_of(ms):
    return ms // SECOND
