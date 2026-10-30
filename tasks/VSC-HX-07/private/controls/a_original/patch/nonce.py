# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Replay protection.

A request may carry ``nonce=N ts=S``: a client-chosen nonce and the client's
timestamp in whole seconds.  The request is fresh when the timestamp lies
within ``replay.skew`` of the gateway clock (either side, inclusive).  A
nonce accepted at time A is remembered for the key that used it until
A + ``replay.window``; while it is remembered the same key cannot use it
again.  Nonces belong to a key: two keys may use the same nonce.
"""
import re

import timeutil
import units
from errors import CommandError, Deny

NONCE_RE = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")


def parse_nonce(text):
    if not NONCE_RE.match(text):
        raise CommandError("bad nonce (1 to 64 characters from A-Z a-z 0-9 _ -)")
    return text


def parse_ts(text):
    return units.parse_int(text, "ts", lo=0, hi=10 ** 11)


def is_fresh(now_ms, ts_s, skew_ms):
    """Whether a client timestamp TS_S (whole seconds) is within SKEW_MS of NOW_MS."""
    return abs(now_ms // units.SECOND - ts_s) * units.SECOND <= skew_ms


class NonceStore:
    def __init__(self, world):
        self.world = world
        self._seen = {}

    def _bucket(self, tenant, keyid):
        return self._seen.setdefault((tenant, keyid), {})

    def _prune(self, bucket, now):
        for nonce in [n for n, until in bucket.items() if timeutil.expired(now, until)]:
            del bucket[nonce]

    def check(self, ctx):
        """Raise Deny or return the commit callable (None when nothing to record)."""
        cfg = self.world.config
        if ctx.nonce is None:
            if cfg.flag(ctx.tenant, "replay.required"):
                raise Deny("nonce-required")
            return None
        if not is_fresh(ctx.now, ctx.ts, cfg.duration_ms(ctx.tenant, "replay.skew")):
            raise Deny("stale")
        bucket = self._bucket(ctx.tenant, ctx.keyid)
        self._prune(bucket, ctx.now)
        if ctx.nonce in bucket:
            raise Deny("replay")
        bucket[ctx.nonce] = timeutil.deadline_after(
            ctx.now, cfg.duration_ms(ctx.tenant, "replay.window"))
        return None

    def remembered(self, tenant, keyid, now):
        bucket = self._seen.get((tenant, keyid), {})
        return sorted(n for n, until in bucket.items() if not timeutil.expired(now, until))

    def forget_key(self, tenant, keyid):
        self._seen.pop((tenant, keyid), None)
