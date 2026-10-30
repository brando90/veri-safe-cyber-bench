# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Sizes: parsing, KiB conversion and display."""
import re

from errors import CommandError

KIB = 1024
MIB = 1024 * KIB
MAX_SIZE = 512 * MIB

_SIZE_RE = re.compile(r"(\d{1,10})(B|KiB|MiB)?")
_FACTOR = {"": 1, "B": 1, "KiB": KIB, "MiB": MIB}


def parse_size(text):
    m = _SIZE_RE.fullmatch(text or "")
    if m is None:
        raise CommandError("bad_size", text)
    n = int(m.group(1)) * _FACTOR[m.group(2) or ""]
    if n > MAX_SIZE:
        raise CommandError("bad_size", text)
    return n


def kib_ceil(nbytes):
    return -(-nbytes // KIB)


def fmt_kib(kib):
    return "%d KiB" % kib


def fmt_bytes(nbytes):
    if nbytes and nbytes % MIB == 0:
        return "%d MiB" % (nbytes // MIB)
    if nbytes and nbytes % KIB == 0:
        return "%d KiB" % (nbytes // KIB)
    return "%d B" % nbytes


def parse_kib(text):
    if not text or not text.isdigit() or len(text) > 9:
        raise CommandError("bad_number", text)
    return int(text)
