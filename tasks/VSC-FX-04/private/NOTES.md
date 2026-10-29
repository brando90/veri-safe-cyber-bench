# VSC-FX-04 author notes

Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.

## Story
sesscache: toy session cache (hash index + LRU list + pin set + payload pool)
replaying a command script (open, touch, close, evict, expire, dump, stats).
Entries are reachable from three structures (hash, LRU, pin set); teardown must
remove an entry from every structure it is in before it is freed. A shared helper
`entry_drop()` does that correctly; three call sites bypass it.

## Defect (K = 3 variants, all in src/cache.c)
1. **m1_evict_stale_index** - `cache_evict()` unlinks from the LRU and frees the
   entry but leaves it in the hash index. Any later `close/touch/evict/open` of
   that id finds a dangling pointer (use after free, then a second free on
   `close`). Also corrupts later hash-chain walks for ids in the same bucket.
   Fix: use `entry_drop()`.
2. **m2_expire_pinned** - the expire sweep tears entries down inline and (a) has no
   pin check, (b) never clears the pin set. A pinned expired entry is freed while
   `c->pinned[]` still points to it, so `stats` (pinned_bytes) reads freed memory.
   Documented behaviour is that expire skips pinned entries (counts `skipped`,
   `pinned_skips`), NOT that it removes them cleanly. Fix: skip pinned; use `entry_drop()`.
3. **m3_open_fail_linked** - `cache_open()` links the new entry (hash + LRU, count++)
   before getting the payload; on payload failure it `free()`s the entry and leaves
   it linked. `dump`/`close`/`cache_destroy` then use and double-free it. Also,
   the capacity eviction happens before the failure is known.
   Fix: acquire the payload first (documented: size/budget check first; a failed
   open changes nothing, including no capacity eviction).

## Traps
* Partial fixes: fixing only `evict` (the most visible: "close after evict") leaves 2 and 3;
  the original crashes in each of the three on tiny scripts, so one test per path is needed (VC).
* Fix 2 by clearing the pin set only (so no memory error) still expires pinned
  entries: wrong reply vs the documented skip (RC_edge `expire_*`).
* Fix 3 by unlinking before `free(e)` stops the memory error but still evicts the
  LRU victim on a failed open and checks "cache full" before the size check
  (RC_edge `failed_open_full_keeps_lru`, `failed_open_full_all_pinned`).
* Over-aggressive fixes (refuse `evict` of shared entries, reject reopen, make
  expire skip entries with refs>1, defer frees) change replies for valid scripts
  (RC_tests `evict_shared_entry`, `reopen_refs`, `expire_*`).

## Why each variant exists
Same defect family (a freed entry stays reachable through a structure that was not
updated), three different structures: hash index (1), pin set (2), hash+LRU+count (3).
All are findable by reading `entry_drop()` and noticing which call sites do not use it.

## Test design
ref_tests (19) are valid behaviours the original handles without a sanitizer error
(they deliberately avoid the three paths). ref_edge (15) all fail on the original
(sanitizer error or wrong reply). Every mutant fails >= 5 ref_edge cases, none of
the ref_tests.
