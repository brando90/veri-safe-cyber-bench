# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Decision log.

Every check appends one entry.  Entries are kept per policy set so that
retention (`log retain N`) can be applied per set; the oldest entries of a
set are dropped first.  Each entry has a global sequence number.

The log keeps request attributes exactly as given, because `log replay`
re-evaluates a logged request against the current policies.  Every path that
prints log data applies secret redaction itself (see render.py).
"""
import heapq

import limits
from errors import LogError


class Entry:
    def __init__(self, seq, time, set_name, subject, action, resource, attrs,
                 effect, by, steps, note):
        self.seq = seq
        self.time = time
        self.set_name = set_name
        self.subject = subject
        self.action = action
        self.resource = resource
        self.attrs = dict(attrs)
        self.effect = effect
        self.by = by
        self.steps = steps
        self.note = note


def _order_key(entry):
    return entry.seq


class DecisionLog:
    def __init__(self):
        self.by_set = {}
        self.next_seq = 1
        self.keep = limits.LOG_KEEP_DEFAULT
        self.dropped = 0

    def record(self, time, set_name, subject, action, resource, attrs, decision):
        entry = Entry(self.next_seq, time, set_name, subject, action, resource, attrs,
                      decision.effect, decision.by, decision.steps, decision.note)
        self.next_seq += 1
        bucket = self.by_set.setdefault(set_name, [])
        bucket.append(entry)
        self._trim(bucket)
        return entry

    def _trim(self, bucket):
        while len(bucket) > self.keep:
            del bucket[0]
            self.dropped += 1

    def retain(self, keep):
        if keep < 1:
            raise LogError("retention must be at least 1")
        self.keep = keep
        for name in sorted(self.by_set):
            self._trim(self.by_set[name])

    def ordered(self):
        """All kept entries, oldest first."""
        buckets = [self.by_set[name] for name in sorted(self.by_set)]
        return list(heapq.merge(*buckets, key=_order_key))

    def get(self, seq):
        for bucket in self.by_set.values():
            for entry in bucket:
                if entry.seq == seq:
                    return entry
        raise LogError("no log entry #%d" % seq)

    def count(self):
        return sum(len(b) for b in self.by_set.values())
