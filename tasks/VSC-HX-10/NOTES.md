# VSC-HX-10 author notes (private)

ledgerkeep is a toy ledger service simulator driven by one long command
stream. It has 25 Python modules (about 1,760 lines) plus a 250-line README
that is the specification. One `World` wires the components:

* `slots`: a 256-slot table. Fresh slots are handed out first, then freed
  slots oldest-first, with the generation bumped and `recycle_hooks` called.
* Per-slot tables in `limits` (the daily tally) and `stats` (ops counters).
* `accounts`, with a minute ring for velocity (`velocity`).
* `ledger` for the money operations.
* `journal` keeps 128-record segments and compacts into `snapshot`, gated
  by `settlement.covers`.
* `txid` ids are `T<epoch>.<seq>` with a 12-bit seq. The packed form is
  used by the journal index, idem and settlement.
* `idem` is a 64-entry LRU built from stamps and a lazy heap.
* `holds` hands out ids H001-H999 with wrap. `timers` is a 1024-bucket
  one-second wheel.
* `settlement` has a 16-entry round-robin table with attempts, backoff and
  parking. `clearing` is scripted.

`invariant.quick` runs after every command (counters only). `invariant.full`
runs on `check` and at end of input (exit 86). `legacy.py` is dead v1 code.

Lever (v4, "long stateful runs"): eight of the ten variants only show after
hundreds to thousands of operations in one run. The smoke examples and
short hand-written scripts never reach those states.

## The defects (K = 10, one mutant each in private/mutants)

| Mutant | Where | Defect | README rule | Ops before it shows |
|---|---|---|---|---|
| M01_recycle_limits | world.py wiring (limits.clear_slot never registered as a recycle hook) | the daily tally lives in a per-slot table and is not cleared when a slot is reused, so a new account inherits the previous owner's `spent_today` (wrong `deny daily`, `balance` line, or limits invariant) | "A newly opened account always starts fresh ... nothing spent today" | >= 257 opens + a close (slot reuse needs all 256 fresh slots used), same day |
| M02_txid_pack | txid.TxId.packed | `epoch * SEQ_MASK + seq` (4095) instead of `epoch << 12 | seq`: T0.4095 and T1.0 collide in the journal index (index invariant), and `from_packed` decodes epoch>=1 ids wrong in replay and batch lines | ids `T0.4095` then `T1.0`; replay prints the original id | 4097 journal records |
| M03_compact_covers | settlement.covers | `seg.last <= next_unassigned` instead of `seg.end <=`: compaction folds a segment whose last record is the first unassigned one; that record never reaches a batch (invariant: folded > assigned) | compaction stops at the first sealed segment with an unassigned record | >= 512 records and the settlement watermark exactly on a segment's last record |
| M04_lru_stamp | idem.IdemCache._evict_one | the stale-heap-pair check compares only presence, not the stamp, so eviction follows first-insertion order and replays do not refresh recency | "Storing a key ... and replaying it both count as a use; least recently used forgotten" | 65 distinct keys with a replay in between |
| M05_idem_scope | ledger._idem_key | key scoped by slot number instead of slot+generation; a later account in a reused slot gets `replay` for the earlier account's keys | "no idempotency keys, even when it reuses the slot" | >= 257 opens + a close, key still in the LRU |
| M06_hold_ids | holds.HoldBook._next_id | after wrap the allocator skips only ids with a pending timer (`timers.pending`), so a live hold without ttl has its id reused and overwritten (held-sum invariant, wrong release) | "skipping ids of live holds" | 999 holds placed with an untimed hold live across the wrap |
| M07_ring_edge | velocity.MinuteRing.count | `m - minute <= 60` instead of `< 60`: a debit made exactly 60 minutes ago still counts (bucket not yet overwritten this minute) | "counts for minutes m..m+59 and no longer from minute m+60 on" | an hour of logical time, debits exactly 60 minutes apart |
| M08_entry_attempts | settlement.Entry.assign | `attempts` not reset when an entry is assigned to a new batch; the batch that reuses the entry 16 batches later inherits the old attempt count (wrong attempt=, retry_at, early parking) | "Every batch has its own attempt count, starting at 0" | 17 batches, the first with failed attempts |
| M09_seal | journal.Journal.append | seal when `index % 128 == 0 and index` instead of `(index + 1) % 128 == 0`: the first segment holds 129 records, `locate` (arithmetic) misses the boundary records, `journal` stats and compaction timing shift | "records 0-127 form the first segment ... sealed as soon as it holds 128" | 129 records |
| M10_wheel | timers.Wheel.due | everything in a swept bucket is expired without comparing the deadline with now, so holds with ttl > 1024 s expire a wheel turn early, and holds due later in the current second expire early | "A hold with until=T expires when the clock reaches T" | ttl > 17 min with the clock passing the bucket, or sub-second positions |

Coverage of the v3/v4 rules:

* Long-run only (hundreds to thousands of ops in one run): M01, M02, M03,
  M04, M05, M06, M08, M09 (8). M07 needs an hour of logical time. M10 needs
  a long ttl.
* Findable by reading one function with the README: M02 (packed vs
  from_packed), M07, M10 (3).
* Need state across 3+ modules: M01 (slots -> world hooks -> limits ->
  ledger/reports), M03 (journal -> settlement -> invariant), M05 (slots ->
  accounts -> ledger -> idem), M06 (holds -> timers -> commands ttl
  optional), M08 (settlement entry table round robin).
* Local patch is wrong, root cause must change: M09 (control g: scanning
  `locate` leaves stats and compaction timing wrong), M02 (control h: tuple
  index keys leave idem/settlement decoding wrong), M05 (control i: scoping
  by name fails t11).

## Intended fix (= private/gold)

* world.py: `self.slots.recycle_hooks.append(self.limits.clear_slot)`. A
  reset in accounts.open on reuse is equivalent.
* `TxId.packed`: `(epoch << SEQ_BITS) | seq`.
* `Settlement.covers`: `seg.end <= next_unassigned`.
* `IdemCache._evict_one`: also require `entry.stamp == stamp`.
* `Ledger._idem_key`: scope by `acct.ident` (slot.gen).
* `HoldBook._next_id`: skip ids in `self.live`.
* `MinuteRing.count`: `m - minute < size`.
* `Entry.assign`: `self.attempts = 0`. Resetting in `release` is
  equivalent.
* `Journal.append`: seal when `(index + 1) % SEGMENT_RECORDS == 0`.
* `Wheel.due`: expire only `deadline <= now`.

## Traps (each caught by a hidden case; see private/CONTROLS.md)

1. Patch `journal.locate` to scan instead of fixing the seal condition:
   e17/e18 and the compaction-timing cases fail (control g).
2. Key the journal index by (epoch, seq) instead of fixing `packed`: e03/e04
   fail on replay and batch lines (control h).
3. Scope idempotency keys by account name: t11 fails, because a reopened
   name must not inherit keys (control i).
4. Reset the slot generation on reuse: t13 and the open lines of e01/e02/e09/
   e10 fail (control e).
5. Count reversals as debits: t03, t06 and smoke s5 fail (control e).
6. Purge an account's idempotency keys at close: t12 fails, because the
   eviction count and order change (control e2).
7. Reuse the lowest freed slot before the fresh ones: t06, t13, t23 fail
   (control e2).
8. Never wrapping hold ids: t14 fails.
9. Fix M03 by refusing to settle or by refusing compaction altogether: t18
   (progressive compaction) and the e05/e06 tails fail.

## Decoys (correct code that looks suspicious)

* `Wheel.due` sets `cursor = now_s` and so revisits the current second on
  the next call. This looks like double processing, but it is needed for
  deadlines later in the same second; expired entries are removed.
* The `Wheel.due` gap branch sweeps only the last `size` seconds after a
  long jump. That covers every bucket exactly once.
* `HoldBook._next_id` ends with `raise InvariantViolation` after the loop.
  This is unreachable: `place` refuses at 500 live holds, which is less
  than 999 ids.
* `Journal.locate` uses arithmetic `(pos - base) // 128`. This is correct
  because sealed segments always hold exactly 128 records and compaction
  drops whole segments.
* The slot generation is never reset on reuse. This is intentional
  (control e).
* Slot reuse is FIFO and only after all fresh slots are used. This is
  documented (control e2).
* Reversals skip the debit rules and may go below the overdraft
  (documented; t03, t06).
* Captures are not debits (documented; t26).
* `IdemCache._tidy` rebuilds the heap from the live entries, dropping stale
  pairs. This is correct.
* `DailyLimits.note/spent_today` reset lazily on `day != today`. This is
  correct.
* `Snapshot._add` drops zero totals. This is correct, because balances
  default to 0.
* Replays do not compare arguments, and refused operations are not stored
  (documented; t09).
* `legacy.py` contains `lowest_free_slot`, a FIFO `FlatRecent` and float
  money formatting. It is dead code that is never imported.

## Notes

* Inputs come from private/make_inputs.py: fixed seeds; the long
  generators drive the gold World in-process only to choose sensible next
  commands. Outputs come from private/build_private.sh (gold run in a fresh
  dir). public/src, the mutants and the control patch trees come from
  private/make_variants.py (exact-text edits of gold).
* The largest input is about 80 KB / 4,600 commands; gold runs every case
  in about 1 s or less.
* The original passes every smoke case and fails all 20 ref_edge cases. It
  also fails 9 ref_tests: the long ordinary streams reach slot reuse,
  segment boundaries, hold wraps or entry reuse.
* M09 is caught by many long cases, because the full check walks the index
  through `locate`. Any long stream the solver writes therefore exits 86 on
  the original until M09 is fixed. That gives away that long runs matter,
  but not where the other nine are.
