# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Recurrence rules: ``FREQ[;key=value]...`` text and its canonical form.

Keys: every (period multiplier), on (weekdays; with a position such as
2TU or -1FR for monthly rules), monthday, count, until.  Parsing accepts
any order, case and blanks; ``text()`` always writes the canonical form.
"""
import re

import civil
import timeparse
from errors import CommandError

FREQS = ("daily", "weekly", "monthly", "yearly")
CODES = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")
TOKEN_RE = re.compile(r"([+-]?[0-9])?(MO|TU|WE|TH|FR|SA|SU)")
KEYS = ("every", "on", "monthday", "count", "until")


class Rule:
    __slots__ = ("freq", "every", "days", "monthday", "count", "until")

    def __init__(self, freq, every=1, days=(), monthday=None, count=None, until=None):
        self.freq = freq
        self.every = every
        self.days = tuple(days)
        self.monthday = monthday
        self.count = count
        self.until = until

    def text(self):
        parts = [self.freq]
        if self.every != 1:
            parts.append("every=%d" % self.every)
        if self.days:
            parts.append("on=" + ",".join(fmt_token(n, wd) for n, wd in self.days))
        if self.monthday is not None:
            parts.append("monthday=%d" % self.monthday)
        if self.count is not None:
            parts.append("count=%d" % self.count)
        if self.until is not None:
            parts.append("until=" + timeparse.format_date(self.until))
        return ";".join(parts)

    def weekdays(self):
        return sorted({wd for _, wd in self.days})


def fmt_token(n, wd):
    return ("%d" % n if n else "") + CODES[wd]


def parse_token(tok):
    m = TOKEN_RE.fullmatch(tok)
    if m is None:
        raise ValueError(tok)
    n = int(m.group(1)) if m.group(1) else 0
    if m.group(1) is not None and not 1 <= abs(n) <= 5:
        raise ValueError(tok)
    return n, CODES.index(m.group(2))


def int_in(text, lo, hi):
    if not text.isdigit() or not lo <= int(text) <= hi:
        raise ValueError(text)
    return int(text)


def parse(text):
    try:
        return _parse(text)
    except (ValueError, CommandError):
        raise CommandError("bad_rule", text) from None


def _parse(text):
    parts = [p.strip() for p in text.split(";")]
    freq = parts[0].lower()
    if freq not in FREQS:
        raise ValueError(text)
    seen = {}
    for part in parts[1:]:
        key, eq, value = part.partition("=")
        key = key.strip().lower()
        if not eq or key not in KEYS or key in seen:
            raise ValueError(part)
        seen[key] = value.strip()
    every = int_in(seen["every"], 1, 400) if "every" in seen else 1
    days = {}
    if "on" in seen:
        if freq not in ("weekly", "monthly"):
            raise ValueError(text)
        for tok in seen["on"].upper().split(","):
            n, wd = parse_token(tok.strip())
            if (freq == "weekly") != (n == 0):
                raise ValueError(tok)
            days[(wd, n)] = (n, wd)
    monthday = None
    if "monthday" in seen:
        if freq != "monthly" or days:
            raise ValueError(text)
        monthday = int_in(seen["monthday"], 1, 31)
    count = int_in(seen["count"], 1, 1000) if "count" in seen else None
    until = timeparse.parse_date(seen["until"]) if "until" in seen else None
    return Rule(freq, every, [days[k] for k in sorted(days)], monthday, count, until)


def canon(text):
    return parse(text).text()
