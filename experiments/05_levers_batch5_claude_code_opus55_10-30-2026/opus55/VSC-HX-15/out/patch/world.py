# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The state of one run."""
from config import Config
from handoffs import Custody
from places import Routes, Sites
from quota import Quota
from readings import Store
from shipments import Shipments


LIMIT = 200


class Audit:
    def __init__(self):
        self.entries = []
        self.seq = 0

    def record(self, line):
        self.seq += 1
        self.entries.append((self.seq, line))
        if len(self.entries) > LIMIT:
            del self.entries[0]

    def tail(self, count=None):
        picked = self.entries if count is None else self.entries[max(0, len(self.entries) - count):]
        return ["#%d %s" % (seq, line) for seq, line in picked]


class World:
    def __init__(self):
        self.config = Config()
        self.sites = Sites()
        self.routes = Routes()
        self.ships = Shipments()
        self.store = Store()
        self.quota = Quota()
        self.audit = Audit()
        self.custody = Custody()
        self.lines = []

    def emit(self, line):
        self.lines.append(line)
