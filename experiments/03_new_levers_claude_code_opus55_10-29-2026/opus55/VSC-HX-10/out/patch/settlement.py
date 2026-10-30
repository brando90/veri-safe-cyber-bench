# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Settlement: journal records are handed to the clearing house in batches.

Outstanding batches occupy entries of a small table; the table is used
round robin.  Records are assigned to batches strictly in journal order;
``next_unassigned`` is the number of the first record not yet in a batch.
"""
import units
from errors import CommandError
from txid import TxId


class Batch:
    __slots__ = ("number", "first_pos", "n", "volume", "first", "last", "state", "entry",
                 "attempts", "created_at")

    def __init__(self, number, records, entry, now):
        self.number = number
        self.first_pos = records[0].index
        self.n = len(records)
        self.volume = sum(r.amount for r in records)
        self.first = records[0].tid.packed()
        self.last = records[-1].tid.packed()
        self.state = "pending"
        self.entry = entry
        self.attempts = 0
        self.created_at = now

    @property
    def label(self):
        return "B%d" % self.number


class Entry:
    __slots__ = ("index", "batch", "attempts", "retry_at")

    def __init__(self, index):
        self.index = index
        self.batch = None
        self.attempts = 0
        self.retry_at = None

    @property
    def busy(self):
        return self.batch is not None

    def assign(self, batch):
        self.batch = batch
        self.attempts = 0
        self.retry_at = None

    def release(self):
        self.batch = None
        self.retry_at = None


class Settlement:
    def __init__(self, world):
        self.world = world
        self.entries = [Entry(i) for i in range(units.SETTLE_ENTRIES)]
        self.last_entry = units.SETTLE_ENTRIES - 1
        self.batches = []
        self.next_unassigned = 0
        self.assigned = 0

    def covers(self, seg):
        return seg.last < self.next_unassigned

    def pending(self):
        return [e.batch for e in self.entries if e.busy]

    def _free_entry(self):
        for step in range(1, units.SETTLE_ENTRIES + 1):
            i = (self.last_entry + step) % units.SETTLE_ENTRIES
            if not self.entries[i].busy:
                self.last_entry = i
                return self.entries[i]
        raise CommandError("settlement backlog full")

    def settle(self):
        w = self.world
        if self.next_unassigned >= w.journal.next_index:
            w.emit("settle nothing")
            return
        entry = self._free_entry()
        records = w.journal.records_from(self.next_unassigned, units.BATCH_MAX)
        batch = Batch(len(self.batches) + 1, records, entry.index, w.clock.now)
        self.batches.append(batch)
        self.next_unassigned = records[-1].index + 1
        self.assigned += batch.n
        entry.assign(batch)
        w.emit("batch %s n=%d volume=%s first=%s last=%s entry=%d" % (
            batch.label, batch.n, units.fmt_money(batch.volume), TxId.from_packed(batch.first),
            TxId.from_packed(batch.last), entry.index))
        self._submit(entry)

    def _submit(self, entry):
        w = self.world
        batch = entry.batch
        if w.clearing.submit(batch):
            batch.state = "settled"
            batch.attempts = entry.attempts + 1
            entry.release()
            w.emit("batch %s settled" % batch.label)
            return
        entry.attempts += 1
        batch.attempts = entry.attempts
        if entry.attempts >= units.MAX_ATTEMPTS:
            batch.state = "parked"
            entry.release()
            w.emit("batch %s parked attempts=%d" % (batch.label, batch.attempts))
            return
        entry.retry_at = w.clock.now + units.RETRY_BASE * 2 ** (entry.attempts - 1)
        w.emit("batch %s failed attempt=%d retry_at=%d" % (batch.label, entry.attempts,
                                                          entry.retry_at))

    def on_clock(self, now):
        due = sorted((e.retry_at, e.batch.number, e.index) for e in self.entries
                     if e.busy and e.retry_at is not None and e.retry_at <= now)
        for _when, _number, i in due:
            entry = self.entries[i]
            entry.retry_at = None
            self._submit(entry)

    def describe(self, batch):
        if batch.state == "pending":
            entry = self.entries[batch.entry]
            return "%s pending n=%d volume=%s attempt=%d retry_at=%d entry=%d" % (
                batch.label, batch.n, units.fmt_money(batch.volume), entry.attempts,
                entry.retry_at, entry.index)
        return "%s %s n=%d volume=%s attempts=%d entry=%d" % (
            batch.label, batch.state, batch.n, units.fmt_money(batch.volume), batch.attempts,
            batch.entry)
