# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The append-only journal.

Records are numbered from 0 in the order they are appended and kept in
segments of ``SEGMENT_RECORDS``.  Sealed segments are folded into the
snapshot by compaction; ``index`` maps packed transaction ids of the live
records to record numbers.
"""
import units
from errors import InvariantViolation
from snapshot import Snapshot


class Record:
    __slots__ = ("index", "tid", "kind", "src", "dst", "src_name", "dst_name", "amount", "at",
                 "reverses", "reversed_by", "hold")

    def __init__(self, tid, kind, src, dst, amount, at):
        self.index = -1
        self.tid = tid
        self.kind = kind
        self.src = None if src is None else src.ident
        self.dst = None if dst is None else dst.ident
        self.src_name = None if src is None else src.name
        self.dst_name = None if dst is None else dst.name
        self.amount = amount
        self.at = at
        self.reverses = None
        self.reversed_by = None
        self.hold = None

    def delta(self, ident):
        d = 0
        if self.src == ident:
            d -= self.amount
        if self.dst == ident:
            d += self.amount
        return d


class Segment:
    __slots__ = ("first", "records", "sealed")

    def __init__(self, first):
        self.first = first
        self.records = []
        self.sealed = False

    @property
    def end(self):
        return self.first + len(self.records)

    @property
    def last(self):
        return self.end - 1


class Journal:
    def __init__(self, world):
        self.world = world
        self.segments = [Segment(0)]
        self.next_index = 0
        self.live_count = 0
        self.folded = 0
        self.compactions = 0
        self.index = {}
        self.snapshot = Snapshot()

    @property
    def active(self):
        return self.segments[-1]

    def append(self, rec):
        rec.index = self.next_index
        self.next_index += 1
        self.live_count += 1
        self.active.records.append(rec)
        self.index[rec.tid.packed()] = rec.index
        if rec.index and rec.index % units.SEGMENT_RECORDS == 0:
            self._seal()

    def _seal(self):
        self.active.sealed = True
        self.segments.append(Segment(self.next_index))
        self._compact()

    def _compact(self):
        sealed = [seg for seg in self.segments if seg.sealed]
        if len(sealed) < units.COMPACT_AFTER:
            return
        n = 0
        for seg in sealed:
            if not self.world.settlement.covers(seg):
                break
            self.snapshot.fold(seg)
            for rec in seg.records:
                del self.index[rec.tid.packed()]
            self.folded += len(seg.records)
            self.live_count -= len(seg.records)
            n += 1
        if n:
            del self.segments[:n]
            self.compactions += 1

    def locate(self, pos):
        for seg in self.segments:
            if seg.first <= pos < seg.end:
                break
        else:
            raise InvariantViolation("journal: record %d is outside the live segments" % pos)
        off = pos - seg.first
        if not 0 <= off < len(seg.records):
            raise InvariantViolation("journal: record %d is not where expected" % pos)
        return seg.records[off]

    def find(self, tid):
        pos = self.index.get(tid.packed())
        if pos is None:
            return None
        return self.locate(pos)

    def records(self):
        for seg in self.segments:
            yield from seg.records

    def records_from(self, pos, limit):
        out = []
        for seg in self.segments:
            if seg.end <= pos:
                continue
            for rec in seg.records[max(0, pos - seg.first):]:
                out.append(rec)
                if len(out) == limit:
                    return out
        return out

    def history(self, ident, limit):
        out = []
        for seg in reversed(self.segments):
            for rec in reversed(seg.records):
                if rec.src == ident or rec.dst == ident:
                    out.append(rec)
                    if len(out) == limit:
                        return out
        return out

    def balances(self):
        totals = dict(self.snapshot.totals)
        for rec in self.records():
            if rec.src is not None:
                totals[rec.src] = totals.get(rec.src, 0) - rec.amount
            if rec.dst is not None:
                totals[rec.dst] = totals.get(rec.dst, 0) + rec.amount
        return totals

    def sealed_count(self):
        return sum(1 for seg in self.segments if seg.sealed)
