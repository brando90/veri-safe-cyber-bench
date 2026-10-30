# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Per-shipment, per-clock-hour intake counter."""
import units


class Quota:
    def __init__(self):
        self.counts = {}
        self.refused = 0

    def admit(self, sid, ts, limit):
        key = (sid, ts // units.HOUR_MS)
        used = self.counts.get(key, 0)
        if limit and used >= limit:
            self.refused += 1
            return False
        self.counts[key] = used + 1
        return True

    def used(self, sid, hour):
        return self.counts.get((sid, hour), 0)
