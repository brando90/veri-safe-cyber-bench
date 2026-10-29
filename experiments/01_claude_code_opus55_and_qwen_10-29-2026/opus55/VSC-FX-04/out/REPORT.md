# VSC-FX-04 root-cause report

All defects are in `src/cache.c`. Every one comes from the same pattern: code that
removes or frees an entry by hand, taking it out of only some of the three
structures that point to it (hash index, LRU list, pin set), or freeing it after it
has already been linked in. The helper `entry_drop()`, which unlinks from all three
and then frees, was used only by `close`, capacity eviction and `cache_destroy`.

1. **`cache_evict`**: it unlinked the entry from the LRU list and freed it, but left
   it in the **hash index**. Any later `touch/close/evict/open` of that id (or a
   lookup of another id in the same bucket) followed the dangling pointer
   (use-after-free, and a double free on a second evict/close).
   Fix: call `entry_drop()`.

2. **`cache_expire`**: it ignored pins. It removed pinned sessions, which breaks the
   contract, and left the freed entry in the **pin set**, so the next `stats` read
   freed memory. `skipped` and `pinned_skips` were never counted.
   Fix: pinned sessions that are old enough are counted in `skipped` and
   `pinned_skips` and left alone. Unpinned ones go through `entry_drop()`.

3. **`cache_open`, failure path**: the entry was put in the hash and LRU and counted
   before the payload was allocated. When `payload_alloc` failed (SIZE 0, >4096, or
   pool over budget), the entry was `free()`d while still linked: `dump`/`stats`/
   lookups then used freed memory, `count` was wrong, and closing it later freed it
   twice. In a full cache the capacity eviction also ran **before** the size/pool
   check, so a failed open still evicted a session.
   Fix: do the size/pool check first, then allocate the entry and payload, then do the
   capacity eviction (if every session is pinned, free the unlinked new entry and
   return `R_FULL`). Link the entry into hash and LRU only once it is fully built.

No reply format changed. The four smoke scripts still give identical output, with
clean ASan/UBSan/LSan.

## Tests (`out/tests/`)
- `evict_then_use`, `evict_then_reopen`, `evict_bucket_neighbour`: evict path.
- `expire_pinned`, `expire_pinned_then_close`, `open_full_all_pinned`: expire with pins.
- `open_fail_size`, `open_fail_pool`, `open_fail_full_cache`: failed-open path
  (bad size, pool budget, no eviction when a full cache gets a failed open).
All 9 crash with heap-use-after-free under ASan on the original and pass on the patch.
