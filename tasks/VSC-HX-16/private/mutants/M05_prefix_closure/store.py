# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The record store and the settings of one run (the world)."""
import stamp
from policy import Policy

DEFAULT_NOW = "2026-01-01T00:00:00Z"
DEFAULT_RETAIN = 30
DEFAULT_WINDOW = 60
DEFAULT_LIMIT = 20
DEFAULT_TOP = 3


class Store:
    def __init__(self):
        self.records = []
        self.next_id = 1
        self.prints = {}
        self.mark = None

    def new_id(self):
        rid = self.next_id
        self.next_id += 1
        return rid

    def add(self, record):
        self.records.append(record)
        self.prints[record.id] = record.fingerprint()

    def get(self, rid):
        for record in self.records:
            if record.id == rid:
                return record
        return None

    def purge(self, now, days):
        """Apply retention; return the removed ids."""
        keep, removed = [], []
        for record in self.records:
            if stamp.older_than(now, record.when, days):
                removed.append(record.id)
            else:
                keep.append(record)
        self.records = keep
        self.mark = (now, days, self.next_id - 1)
        return removed

    def sources(self):
        return sorted({r.source for r in self.records})


class World:
    def __init__(self, out):
        self.out = out
        self.now = stamp.parse(DEFAULT_NOW)
        self.retain = DEFAULT_RETAIN
        self.window = DEFAULT_WINDOW
        self.limits = {}
        self.default_limit = DEFAULT_LIMIT
        self.top = DEFAULT_TOP
        self.policy = Policy()
        self.store = Store()

    def limit_for(self, source):
        return self.limits.get(source, self.default_limit)
