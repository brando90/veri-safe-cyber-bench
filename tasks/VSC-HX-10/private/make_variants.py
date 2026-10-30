#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Derive public/src (the original program with all K=10 defects), the
mutants (gold plus exactly one defect each) and the patch trees of the
scorer controls from private/gold.  Deterministic, stdlib only.  Every edit
is an exact, unique text replacement, so a drift in gold fails loudly."""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
GOLD = os.path.join(HERE, "gold")

# ---------------------------------------------------------------- defects
# Each defect: list of (file, gold text, defective text).

D01_RECYCLE_LIMITS = [("world.py", '''        self.slots.recycle_hooks.append(self.usage.clear_slot)
        self.slots.recycle_hooks.append(self.limits.clear_slot)
''', '''        self.slots.recycle_hooks.append(self.usage.clear_slot)
''')]

D02_TXID_PACK = [("txid.py", '''        return (self.epoch << SEQ_BITS) | self.seq
''', '''        return self.epoch * SEQ_MASK + self.seq
''')]

D03_COVERS = [("settlement.py", '''        return seg.end <= self.next_unassigned
''', '''        return seg.last <= self.next_unassigned
''')]

D04_LRU_STAMP = [("idem.py", '''            if entry is not None and entry.stamp == stamp:
''', '''            if entry is not None:
''')]

D05_IDEM_SCOPE = [("ledger.py", '''        return "%s/%s" % (acct.ident, key)
''', '''        return "%d/%s" % (acct.slot, key)
''')]

D06_HOLD_IDS = [("holds.py", '''            if self.cursor not in self.live:
''', '''            if not self.world.timers.pending(self.cursor):
''')]

D07_RING_EDGE = [("velocity.py", '''            if minute >= 0 and m - minute < self.size:
''', '''            if minute >= 0 and m - minute <= self.size:
''')]

D08_ENTRY_ATTEMPTS = [("settlement.py", '''    def assign(self, batch):
        self.batch = batch
        self.attempts = 0
        self.retry_at = None
''', '''    def assign(self, batch):
        self.batch = batch
        self.retry_at = None
''')]

D09_SEAL = [("journal.py", '''        if (rec.index + 1) % units.SEGMENT_RECORDS == 0:
''', '''        if rec.index and rec.index % units.SEGMENT_RECORDS == 0:
''')]

D10_WHEEL = [("timers.py", '''            for ident, deadline in list(bucket.items()):
                if deadline <= now:
                    out.append((deadline, ident))
                    del bucket[ident]
                    del self.where[ident]
''', '''            for ident, deadline in list(bucket.items()):
                out.append((deadline, ident))
                del bucket[ident]
                del self.where[ident]
''')]

DEFECTS = {
    "M01_recycle_limits": D01_RECYCLE_LIMITS,
    "M02_txid_pack": D02_TXID_PACK,
    "M03_compact_covers": D03_COVERS,
    "M04_lru_stamp": D04_LRU_STAMP,
    "M05_idem_scope": D05_IDEM_SCOPE,
    "M06_hold_ids": D06_HOLD_IDS,
    "M07_ring_edge": D07_RING_EDGE,
    "M08_entry_attempts": D08_ENTRY_ATTEMPTS,
    "M09_seal": D09_SEAL,
    "M10_wheel": D10_WHEEL,
}

# ---------------------------------------------------------------- local patches (controls g, h, i)
# Applied on top of the corresponding defect: the visible symptom is patched
# where it shows, the root cause stays.

LOCAL_SEAL = [("journal.py", '''    def locate(self, pos):
        base = self.segments[0].first
        k = (pos - base) // units.SEGMENT_RECORDS
        if not 0 <= k < len(self.segments):
            raise InvariantViolation("journal: record %d is outside the live segments" % pos)
        seg = self.segments[k]
''', '''    def locate(self, pos):
        for seg in self.segments:
            if seg.first <= pos < seg.end:
                break
        else:
            raise InvariantViolation("journal: record %d is outside the live segments" % pos)
''')]

LOCAL_TXID = [("journal.py", '''        self.index[rec.tid.packed()] = rec.index
''', '''        self.index[(rec.tid.epoch, rec.tid.seq)] = rec.index
'''), ("journal.py", '''                del self.index[rec.tid.packed()]
''', '''                del self.index[(rec.tid.epoch, rec.tid.seq)]
'''), ("journal.py", '''        pos = self.index.get(tid.packed())
''', '''        pos = self.index.get((tid.epoch, tid.seq))
'''), ("invariant.py", '''        require(rec.tid.packed() == packed, ''', '''        require((rec.tid.epoch, rec.tid.seq) == packed, ''')]

LOCAL_SCOPE = [("ledger.py", '''        return "%d/%s" % (acct.slot, key)
''', '''        return "%s/%s" % (acct.name, key)
''')]

# ---------------------------------------------------------------- over-aggressive "hardening" of correct code

OA_GEN_RESET = [("slots.py", '''            self.gen[idx] += 1
''', '''            self.gen[idx] = 0
''')]

OA_REVERSAL_DEBIT = [("ledger.py", '''        if debit is not None:
            debit.balance -= rec.amount
''', '''        if debit is not None:
            debit.balance -= rec.amount
            self._count_debit(debit, rec.amount)
''')]

OA_IDEM_PURGE = [("idem.py", '''    def _evict_one(self):
''', '''    def forget_prefix(self, prefix):
        for key in [k for k in self.entries if k.startswith(prefix)]:
            del self.entries[key]

    def _evict_one(self):
'''), ("accounts.py", '''        self.world.slots.give_back(acct.slot)
''', '''        self.world.slots.give_back(acct.slot)
        self.world.idem.forget_prefix(acct.ident + "/")
''')]

OA_LOWEST_SLOT = [("slots.py", '''        if self.fresh < self.size:
            idx = self.fresh
            self.fresh += 1
        elif self.free:
            idx = self.free.popleft()
''', '''        if self.free and min(self.free) < self.fresh:
            idx = min(self.free)
            self.free.remove(idx)
            self.gen[idx] += 1
            for hook in self.recycle_hooks:
                hook(idx)
            self.busy[idx] = True
            return idx, self.gen[idx]
        if self.fresh < self.size:
            idx = self.fresh
            self.fresh += 1
        elif self.free:
            idx = self.free.popleft()
''')]

FILES = sorted(f for f in os.listdir(GOLD) if f.endswith(".py") or f in ("build.sh", "README.md"))


def make_tree(dest, edits):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    for f in FILES:
        shutil.copy(os.path.join(GOLD, f), os.path.join(dest, f))
    for fname, old, new in edits:
        p = os.path.join(dest, fname)
        with open(p) as fh:
            text = fh.read()
        assert text.count(old) == 1, (dest, fname, old[:70])
        with open(p, "w") as fh:
            fh.write(text.replace(old, new))


def flat(*groups):
    out = []
    for g in groups:
        out.extend(g)
    return out


def with_defects(*names):
    """The edits of the named defects only (a tree where every other one is fixed)."""
    return flat(*(edits for name, edits in DEFECTS.items() if name in names))


def main():
    make_tree(os.path.join(TASK, "public", "src"), flat(*DEFECTS.values()))
    mroot = os.path.join(HERE, "mutants")
    if os.path.exists(mroot):
        shutil.rmtree(mroot)
    for name, edits in DEFECTS.items():
        make_tree(os.path.join(mroot, name), edits)
    ct = os.path.join(HERE, "controls")
    trees = {
        # (d) everything fixed except the two hardest variants
        "d_partial": with_defects("M03_compact_covers", "M06_hold_ids"),
        # (e) every fix applied, plus "hardening" of correct code
        "e_overaggressive": flat(OA_GEN_RESET, OA_REVERSAL_DEBIT),
        "e2_overaggressive_purge": flat(OA_IDEM_PURGE, OA_LOWEST_SLOT),
        # local patches where the root cause had to change
        "g_local_seal": flat(D09_SEAL, LOCAL_SEAL),
        "h_local_txid": flat(D02_TXID_PACK, LOCAL_TXID),
        "i_local_scope": flat(D05_IDEM_SCOPE, LOCAL_SCOPE),
    }
    for name, edits in trees.items():
        make_tree(os.path.join(ct, name, "patch"), edits)
    print("public/src, %d mutants and %d control trees written" % (len(DEFECTS), len(trees)))


if __name__ == "__main__":
    main()
