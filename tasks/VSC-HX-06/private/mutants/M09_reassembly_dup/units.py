# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Unit constants and conversions.

relaydesk keeps every instant and every duration as an integer number of
milliseconds, and every size as an integer number of bytes.  Values in other
units (configuration keys ending in ``_s``, ``_min`` or ``_kib``, retry-after
hints from the link, the billing rate per KiB) are converted at the edge with
the helpers below, never by hand.
"""

MS_PER_S = 1000
S_PER_MIN = 60
MIN_PER_HOUR = 60
HOUR_PER_DAY = 24

MS_PER_MIN = MS_PER_S * S_PER_MIN
MS_PER_HOUR = MS_PER_MIN * MIN_PER_HOUR
MS_PER_DAY = MS_PER_HOUR * HOUR_PER_DAY
MIN_PER_DAY = MIN_PER_HOUR * HOUR_PER_DAY

BYTES_PER_KIB = 1024
# Decimal kilobytes.  Only the v1 spool format (legacy.py) counted in these.
BYTES_PER_KB = 1000


def s_to_ms(seconds):
    return seconds * MS_PER_S


def min_to_ms(minutes):
    return minutes * MS_PER_MIN


def ms_to_s_floor(ms):
    return ms // MS_PER_S


def kib_to_bytes(kib):
    return kib * BYTES_PER_KIB


def kb_to_bytes(kb):
    """Decimal kilobytes (legacy v1 quotas)."""
    return kb * BYTES_PER_KB


def bytes_to_kib_ceil(nbytes):
    """Started KiB: 1..1024 bytes -> 1, 1025 -> 2, 0 -> 0."""
    return -(-nbytes // BYTES_PER_KIB)


# Multipliers from a configuration unit to the internal unit of its kind.
TIME_SCALE = {"ms": 1, "s": MS_PER_S, "min": MS_PER_MIN}
SIZE_SCALE = {"bytes": 1, "kib": BYTES_PER_KIB}
