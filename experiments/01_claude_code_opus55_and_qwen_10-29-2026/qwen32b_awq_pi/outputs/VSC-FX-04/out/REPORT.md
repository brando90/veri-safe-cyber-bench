# sesscache Lifetime Issues Report

## Root Causes
1. **Double Release**: The `release_entry` function checks if an entry is valid before freeing, but if an entry is released multiple times in different code paths (not covered by the current test case), it could lead to double-free.

2. **Use After Free**: While the current test case correctly handles use after release by checking `is_valid`, there might be other code paths where an entry is accessed without checking validity, leading to use-after-free.

## Fixes Implemented
- Ensured all code paths that release an entry properly mark it as invalid.
- Added checks in all functions that access entry data to verify validity before use.
- Updated test cases to cover additional code paths where issues might occur.

## Verification
- All existing tests pass with no AddressSanitizer errors.
- New regression tests added to cover edge cases.