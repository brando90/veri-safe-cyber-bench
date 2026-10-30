# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Durations: text to whole seconds and back.

Text is one or more ``<count><unit>`` parts in descending unit order
(``1d2h3m4s``) or a single decimal part (``1.5h``).  Decimal results are
rounded to whole seconds, halves up.
"""
import re
from fractions import Fraction

from errors import CommandError

UNITS = (("d", 86400), ("h", 3600), ("m", 60), ("s", 1))
SECONDS = dict(UNITS)
MAX_SECONDS = 400 * 86400
PART_RE = re.compile(r"(\d+)([dhms])")
DECIMAL_RE = re.compile(r"(\d+\.\d{1,6})([dhms])")


def parse(text):
    m = DECIMAL_RE.fullmatch(text)
    if m is not None:
        exact = Fraction(m.group(1)) * SECONDS[m.group(2)]
        total = (exact + Fraction(1, 2)).__floor__()
    else:
        total = 0
        pos = 0
        last = -1
        while pos < len(text):
            part = PART_RE.match(text, pos)
            if part is None:
                raise CommandError("bad_duration", text)
            rank = [u for u, _ in UNITS].index(part.group(2))
            if rank <= last:
                raise CommandError("bad_duration", text)
            last = rank
            total += int(part.group(1)) * SECONDS[part.group(2)]
            pos = part.end()
        if pos == 0:
            raise CommandError("bad_duration", text)
    if total > MAX_SECONDS:
        raise CommandError("bad_duration", text)
    return total


def fmt(seconds):
    if seconds == 0:
        return "0s"
    out = []
    for unit, size in UNITS:
        count, seconds = divmod(seconds, size)
        if count:
            out.append("%d%s" % (count, unit))
    return "".join(out)
