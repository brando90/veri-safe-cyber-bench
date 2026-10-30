# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Helpers kept from the v1 command set.

v1 used colon-separated credentials (``TENANT:KEYID:SECRET``), a token
bucket instead of windows, and decimal kilobytes in its reports.  None of
this is wired into the v2 dispatcher; it is kept because external tooling
still imports ``parse_v1_credential`` and ``kb_decimal`` to read old logs.
"""
import units


def parse_v1_credential(text):
    """(tenant, keyid, secret) of a v1 credential, or None."""
    parts = text.split(":")
    if len(parts) != 3 or not all(parts):
        return None
    return parts[0], parts[1], parts[2]


def to_v2_credential(text):
    parts = parse_v1_credential(text)
    if parts is None:
        return None
    return ".".join(parts)


def kb_decimal(nbytes):
    """v1 reports: decimal kilobytes, rounded up."""
    return (nbytes + 999) // 1000


class TokenBucket:
    """v1 limiter: CAPACITY tokens, refilled at RATE tokens per second."""

    def __init__(self, capacity, rate):
        self.capacity = capacity
        self.rate = rate
        self.tokens = capacity
        self.stamp = 0

    def _refill(self, now):
        elapsed = now - self.stamp
        if elapsed > 0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate // units.SECOND)
            self.stamp = now

    def take(self, now):
        self._refill(now)
        if self.tokens <= 0:
            return False
        self.tokens -= 1
        return True


def retry_after_v1(cfg, tenant):
    """v1 always told clients to wait one full window."""
    return cfg.seconds(tenant, "rate.window")


def format_v1_usage(tenant, requests, nbytes):
    return "%s:%d:%dkB" % (tenant, requests, kb_decimal(nbytes))
