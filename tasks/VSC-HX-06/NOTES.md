# VSC-HX-06 author notes (private)

relaydesk: a toy message-delivery simulator on a logical clock (milliseconds
from `d0 00:00:00.000`). 35 Python modules (about 3,000 lines in gold) plus a
README that is the specification. Commands come in on stdin; dispatch rounds
run at multiples of `dispatch.interval_ms`, and when a round does nothing the
dispatcher skips ahead to the next wakeup. After every command the
consistency check (invariant.py) compares counters with message states,
queue services with attempts, per-recipient sums, billing lines with
deliveries, and reassembly sizes. A violation prints `INVARIANT: ...` and
exits 86.

The defects are ordinary logic and consistency defects only: no
memory-safety, path or injection defects, and no input that crashes the
program.

## The defects (K = 12, one mutant each in private/mutants)

| Mutant | Where | Defect | README rule it breaks | Difficulty |
|---|---|---|---|---|
| M01_retry_place | dispatch.settle (RETRY branch) | a retried fragment is taken out of the queue and re-added, so it gets a new queue order and falls behind later messages | "a fragment keeps its message's place, retries included" | hard: the requeue looks like natural bookkeeping |
| M02_turn_stamp | queueing.mark_served | the sender's turn is stamped with the clock (`now`) instead of the service counter, so senders served in the same round tie and fall back to queue order | sender fairness: least recently served sender first, attempts totally ordered | hard: only visible with several senders in one round |
| M03_window_edge | timewin.within (shared helper) | `<=` instead of `<`: an event exactly W ago is still in the window (dedup, rolling hour, `hour=` stats, forecast) | "exactly 60 minutes ago no longer counts", duplicates "less than" the window | medium; **shared helper**: patching dedup.find alone leaves the hourly limit wrong (e06) |
| M04_ttl_retry_edge | retry.decide | expires only if the retry instant is after the deadline; a retry due exactly at the deadline is scheduled and then expires in the queue | "expire if the retry instant is at or after the deadline" | medium (off-by-one at the TTL edge) |
| M05_busy_units | dispatch.settle | the link's busy hint (seconds) is used as milliseconds | busy waits at least SECONDS | easy-medium (unit mismatch) |
| M06_kib_scale | units.SIZE_SCALE | `kib` is scaled by the legacy 1000-byte kB | 1 KiB = 1024 bytes | medium (`kb_to_bytes` exists for legacy.py, which is a decoy) |
| M07_batch_capacity | commands.cmd_batch + intake.submit | batch checks the recipient's capacity once before the block and skips it per line, so a batch can overfill a recipient (exit 86 via check_capacity) | the acceptance checks apply to every message, whichever command submits it | medium: limit enforced on one entry point only |
| M08_direct_reset | dispatch.attempt / settle | the failures-in-row counter is reset on success only on the round path; a successful direct attempt leaves the count, so a later failure pauses the recipient too early | failures in a row reset on any acknowledged attempt | hard: counter reset in one path only |
| M09_reassembly_dup | reassembly.Buffer.add | the duplicate-index guard is missing; after a lost ack the resent fragment is counted twice and the message completes with a gap (exit 86 via check_reassembly, or a wrong body) | in-order reassembly, a duplicate is ignored | medium: fragment reassembly gap |
| M10_dedup_rejected | intake.submit / accept | dedup uses `check` (find and remember) before the capacity check, so a rejected submission is remembered and blocks a valid resend | "only accepted messages are remembered" | medium-hard: stale state between calls |
| M11_money_total | money.total (shared helper) | totals are rounded once on the exact sum instead of summing rounded lines (invoice total, revenue, plans, senders report) | "totals are sums of rounded lines" | medium; **shared helper**: patching only the invoice total leaves stats/plans/reports wrong (e16) |
| M12_direct_limits | intake.try_direct | the direct (urgent, single-fragment) path skips the daily/hourly/volume limits | "These rules hold for every path that can start a message" | medium: limit enforced on one entry point only |

Required categories: ordering/tie-break (M01, M02); window and TTL edges
(M03, M04); units (M05 ms vs s, M06 KiB vs kB); stale state (M10); counter
reset in one path only (M08); aggregate rounding (M11); reassembly gap (M09);
limit on one entry point only (M07, M12); shared helper where the obvious
local patch is wrong (M03, M11).

## Intended fix (= private/gold)

* settle RETRY: only `frag.not_before = decision.at`; the queue entry stays.
* mark_served: `self._turn[sender] = self._services`.
* timewin.within: `now - earlier < width_ms`.
* retry.decide: `if at >= msg.deadline: EXPIRE`.
* settle: `hint = units.s_to_ms(outcome.after_s)`.
* units: `SIZE_SCALE["kib"] = BYTES_PER_KIB`.
* batch: no pre-check; `intake.submit(svc, req)` per line (full checks).
* settle: `svc.breaker.on_success(r)` on every acknowledged attempt (direct and round).
* Buffer.add: `if index in self.parts: return False`.
* submit: `dedup.find` before the capacity check; `dedup.remember` only in accept.
* money.total: `sum(cents(a) for a in amounts)`.
* try_direct: return False when `limits.block_reason(...)` is not None.

## Decoys (look wrong, are correct)

1. Urgent messages ignore quiet hours in `Dispatcher.eligible` and `explain` (documented).
2. A duplicate does not refresh the dedup window (documented; OA_DEDUP_REFRESH breaks t06).
3. `money.cents` rounds half up with integer `(2n+d)//(2d)` rather than `round()` (half to even would be wrong; OA_ROUNDING).
4. `fragment.split_bytes` moves the cut back over continuation bytes with no lower-bound check: safe because `frag.size_bytes >= 4`.
5. `localtime.local_day` uses floor division, so day -1 exists for western offsets early on d0 (documented).
6. `in_window` with start > end wraps over midnight, and `Config.quiet` returns None when start == end.
7. Audit values are written unquoted: every value is a validated name, id or number.
8. `retry.backoff_ms` raises the factor to an unbounded-looking power: the attempt count is bounded by `retry.max_attempts` and the result is capped.
9. Limits are checked only for messages that have not started (documented; OA_LIMITS_ALWAYS breaks t08).
10. `units.kb_to_bytes` / `dedup.check` exist and are used only by the dead v1 spool code in legacy.py.

## Traps (each caught by a hidden case; see private/CONTROLS.md)

1. Fixing M03 only in dedup.find (control d2): e06 (hourly limit at exactly one hour) still fails.
2. Fixing M11 only in the invoice total (control d2): e16 (stats revenue, plans, senders report) still fails.
3. Making urgent respect quiet hours or refreshing the dedup window (control e1): t05/t06 fail.
4. Switching cents() to `round()` (control e2): every half-cent line changes.
5. Applying limits to fragments of started messages (control e3): t08 fails.
6. M08: the round path looks right on its own; the failing behaviour needs a direct (urgent, single-fragment) success between round-path failures (e12).
7. M07 "fixed" by keeping the pre-check and also checking per line: a batch into a full recipient prints `ERROR batch: recipient rx has no room` instead of the per-line `REJECT b1 queue-full` (e11).

## Notes

* Original: passes every smoke case, fails every ref_edge case (19/19) and 12 of 26 ref_tests.
* Every mutant fails at least one ref_edge case and no smoke case (check_variants.py; output in CONTROLS.md).
* t12_big_input (120 messages over two days) takes about 0.8 s CPU on gold.
* build_private.sh regenerates public/src, the mutants, the control trees and every expected output from gold deterministically.
