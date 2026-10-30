# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Reading store, one time-ordered list per shipment."""
from bisect import bisect_left, bisect_right
from collections import namedtuple

Reading = namedtuple("Reading", "ts temp hum")


def _ts(reading):
    return reading.ts


class Store:
    def __init__(self):
        self.rows = {}

    def all(self, sid):
        return self.rows.get(sid, [])

    def has(self, sid, ts):
        rs = self.all(sid)
        i = bisect_left(rs, ts, key=_ts)
        return i < len(rs) and rs[i].ts == ts

    def put(self, sid, reading):
        rs = self.rows.setdefault(sid, [])
        i = bisect_left(rs, reading.ts, key=_ts)
        if i < len(rs) and rs[i].ts == reading.ts:
            rs[i] = reading
            return False
        rs.insert(i, reading)
        return True

    def drop_before(self, sid, cutoff):
        rs = self.all(sid)
        i = bisect_right(rs, cutoff, key=_ts)
        del rs[:i]
        return i

    def replace_all(self, sid, rows):
        self.rows[sid] = list(rows)
        return len(rows)

    def clear(self, sid):
        self.rows.pop(sid, None)

    def total(self):
        return sum(len(rs) for rs in self.rows.values())
