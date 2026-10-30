# VSC-HX-10 ledgerkeep: root causes and fixes

All fixes are in `out/patch/` (a full copy of `src/` with these changes). The smoke tests still pass.

| # | File | Root cause | Fix |
|---|------|-----------|-----|
| 1 | world.py | When a slot was handed out again, only the `ops` counters were cleared. The daily-limit tally (kept per slot) was carried over, so a new account started with the old account's `spent_today`. That can trip `limits: ... spent ... today` (exit 86). | Also register `limits.clear_slot` as a slot recycle hook. |
| 2 | ledger.py | Idempotency keys were stored per *slot* (`slot/key`), so a new account in a reused slot inherited the old account's keys and got false `replay` lines. | Store keys per account identity (`slot.gen/key`). |
| 3 | txid.py | `packed()` used `epoch * SEQ_MASK` (4095) where `from_packed` expects `epoch << 12`. So T1.0 collided with T0.4095 in the journal index. That broke `show`/`reverse`, gave wrong ids in replay and batch lines, and failed the index count check after id 4096. | `(epoch << SEQ_BITS) \| seq`. |
| 4 | velocity.py | The window test `m - minute <= 60` still counted a debit in minute m+60. The README says it counts for m..m+59. | `0 <= m - minute < size`. |
| 5 | holds.py | A new hold id skipped only ids that had a pending *timer*. A live hold with no ttl could get its id reused, which overwrote the live hold and made `held` inconsistent (exit 86). | Skip ids found in `self.live`. |
| 6 | timers.py | The timing wheel expired everything in a visited one-second bucket. That included deadlines later in the same second (expired up to 999 ms early) and deadlines one or more wheel laps (1024 s) ahead, which matters because ttl can be up to 1d. | Only take entries with `deadline <= now` and leave the rest in their bucket. |
| 7 | journal.py | A segment was sealed when record index 128, 256, ... was appended, so the first segment held 129 records. That broke `sealed`/`segments` counts and `locate()` (`record N is not where expected`, exit 86). | Seal when the active segment holds 128 records. |
| 8 | settlement.py | `covers()` used `seg.last <= next_unassigned`, so compaction folded a segment whose last record was not yet in a batch (folded > assigned, exit 86). | `seg.last < next_unassigned`. |
| 9 | settlement.py | The attempt count lived on the table entry and was never reset. A batch that reused an entry started with the previous batch's attempts, which gave wrong `attempt=`/`retry_at=` and early parking. | Reset `attempts = 0` in `Entry.assign`. |
| 10 | idem.py | LRU eviction popped heap entries without checking they were current. A stale (older) stamp for a key that had since been replayed evicted that recently used key instead of the true LRU key. | Evict only when the popped stamp equals the entry's current stamp. |
| 11 | units.py | The money regex allowed only 9 integer digits, so the documented maximum balance amount `1000000000` (and an overdraft of that size) was refused as `bad amount`. The `amount too large` check below it could never trigger. | Allow 10 digits. The existing `> MAX_MONEY` check still applies. |

## Tests (`out/tests/`, 10 pairs)

The expected outputs come from the patched build. I checked each test against variants of the patched build with one fix reverted at a time, and every fix is caught by at least one test.

- `slot_reuse_fresh_account`: fixes 1 and 2 (256 slots used, then reuse).
- `txid_epoch_rollover`: fix 3 (plus 7).
- `velocity_hour_window`: fix 4.
- `hold_id_wrap_skips_live`: fix 5.
- `hold_expiry_deadline`: fix 6 (same-second deadline and a 1d ttl across wheel laps).
- `segment_seal_and_compaction`: fix 7 (seal at 128, compaction, show/reverse of compacted records).
- `compaction_unassigned_boundary`: fix 8.
- `batch_attempts_per_batch`: fix 9.
- `idem_lru_replay_counts`: fix 10.
- `money_max_balance`: fix 11.
