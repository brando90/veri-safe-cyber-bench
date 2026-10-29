# sesscache Lifetime Fix Report

## Root Cause

The `cache_evict` function did not remove the session entry from the hash table before destroying it. This left a dangling pointer in the hash index, allowing subsequent operations (like `close ID`) to reference an already-freed object. This caused:

1. Double-free vulnerabilities when evicting/closing the same ID
2. Use-after-free when operating on evicted sessions

## Fix

In `cache_evict`, added `hash_remove(c, e);` before destroying the entry to fully remove all references to the session. This ensures:

- The hash index is cleaned up
- No future lookups can find the evicted session
- Operations on evicted IDs correctly return `error: no such session`

## Verification

Test case `test_evict_after.in` verifies the fix:

```text
open A 16
ok evicted A
close A
error: no such session
```

The original implementation would have crashed or shown undefined behavior on the second `close A` command. The fixed version correctly handles it as an invalid operation on an evicted session.