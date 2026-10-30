# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""relaydesk v1 compatibility (not reachable from the command table).

Version 1 kept a single FIFO per recipient and wrote spool files with one
record per line:

    v1|ID|SENDER|RECIPIENT|QUOTA_KB|TTL_S|BODY

QUOTA_KB was a per-message size limit in decimal kilobytes.  The v2
dispatcher does not read spool files any more; this module is kept so that
old spool files can still be inspected by maintenance scripts, and its
helpers are exercised by nothing in the command path.
"""

import units
import timefmt
from errors import CommandError

V1_FIELDS = 7


class V1Record:
    __slots__ = ("msg_id", "sender", "recipient", "quota_bytes", "ttl_ms", "body")

    def __init__(self, msg_id, sender, recipient, quota_bytes, ttl_ms, body):
        self.msg_id = msg_id
        self.sender = sender
        self.recipient = recipient
        self.quota_bytes = quota_bytes
        self.ttl_ms = ttl_ms
        self.body = body


def parse_v1(text):
    """Parse one v1 spool line.  The body is the remainder after the sixth
    '|', so it may itself contain '|'."""
    parts = text.split("|", V1_FIELDS - 1)
    if len(parts) != V1_FIELDS or parts[0] != "v1":
        raise CommandError("not a v1 record")
    _, msg_id, sender, recipient, quota, ttl, body = parts
    if not quota.isdigit() or not ttl.isdigit():
        raise CommandError("bad v1 numbers")
    return V1Record(msg_id, sender, recipient, units.kb_to_bytes(int(quota)),
                    units.s_to_ms(int(ttl)), body)


def fits_quota(record):
    return len(record.body.encode("utf-8")) <= record.quota_bytes


class V1Queue:
    """The v1 per-recipient FIFO: no priorities, no fairness, no fragments."""

    def __init__(self):
        self._fifo = {}

    def push(self, record):
        self._fifo.setdefault(record.recipient, []).append(record)

    def pop(self, recipient):
        q = self._fifo.get(recipient)
        if not q:
            return None
        return q.pop(0)

    def depth(self, recipient):
        return len(self._fifo.get(recipient, ()))

    def recipients(self):
        return sorted(self._fifo)


def replay(records, dedup, window_ms, now):
    """v1 replay order: file order, duplicates dropped with the combined
    check-and-remember of the dedup store (v1 had no capacity limit)."""
    kept, dropped = [], []
    for rec in records:
        key = dedup.key(rec.sender, rec.recipient, rec.body)
        if dedup.check(key, now, window_ms, rec.msg_id) is None and fits_quota(rec):
            kept.append(rec)
        else:
            dropped.append(rec)
    return kept, dropped


def describe(record):
    return "v1 %s %s->%s quota=%dB ttl=%s" % (
        record.msg_id, record.sender, record.recipient, record.quota_bytes,
        timefmt.fmt_seconds(record.ttl_ms))


def v1_backoff_ms(attempt):
    """v1 retried every 5 s, then every 30 s from the third attempt on."""
    return units.s_to_ms(5 if attempt < 3 else 30)


def v1_to_request_fields(record, default_prio="normal"):
    """Fields of a v2 send line for a v1 record (v1 had no priorities)."""
    return (record.msg_id, record.sender, record.recipient, default_prio,
            record.ttl_ms, record.body)


def v1_summary(records):
    """Per-recipient count and decimal-kilobyte volume of v1 records, as the
    v1 nightly report printed them (sizes rounded up to whole KB)."""
    per = {}
    for rec in records:
        n, kb = per.get(rec.recipient, (0, 0))
        size = len(rec.body.encode("utf-8"))
        per[rec.recipient] = (n + 1, kb + -(-size // units.BYTES_PER_KB))
    return ["%s %d %dKB" % (r, n, kb) for r, (n, kb) in sorted(per.items())]


def drain_v1(queue, recipient, budget_kb):
    """v1 delivery loop: pop records while the decimal-KB budget lasts."""
    sent = []
    left = units.kb_to_bytes(budget_kb)
    while True:
        rec = queue.pop(recipient)
        if rec is None:
            break
        size = len(rec.body.encode("utf-8"))
        if size > left:
            queue._fifo.setdefault(recipient, []).insert(0, rec)
            break
        left -= size
        sent.append(rec)
    return sent
