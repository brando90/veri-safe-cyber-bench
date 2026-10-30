# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Totals of the journal records that compaction has folded away."""


class Snapshot:
    def __init__(self):
        self.totals = {}
        self.records = 0
        self.volume = 0
        self.last = None

    def fold(self, segment):
        for rec in segment.records:
            if rec.src is not None:
                self._add(rec.src, -rec.amount)
            if rec.dst is not None:
                self._add(rec.dst, rec.amount)
            self.volume += rec.amount
            self.records += 1
            self.last = rec.tid

    def _add(self, ident, delta):
        value = self.totals.get(ident, 0) + delta
        if value:
            self.totals[ident] = value
        else:
            self.totals.pop(ident, None)

    def total(self, ident):
        return self.totals.get(ident, 0)
