# Root Cause Analysis for Logpack Length Check Fix

## Summary

The original `logpack` tool did not fully validate that declared record lengths in the archive matched the actual available bytes, leading to potential buffer overreads and incorrect outputs. The fix ensures every length read from the archive is checked against the remaining bytes, rejecting malformed archives with the documented `error: truncated archive` (exit 2).

## Root Causes

1. **Header and Length Separation**: The 4-byte header (1 byte for record type, 3 bytes for length) was read without verifying that the declared length did not exceed the remaining bytes in the archive.
2. **Missing Pre-Consumption Check**: Before processing a record's data payload, the code did not check if `length <= remaining_bytes`. This allowed reading past the end of the buffer, triggering AddressSanitizer errors or incorrect outputs.
3. **No Trailing Bytes Check**: After processing all records, the code did not verify that no trailing bytes remained, which could indicate a malformed archive.

## Fixes

1. **Pre-Consumption Length Check**: Added a check before processing each record's data to ensure `length <= remaining_bytes`. If not, the program exits with `error: truncated archive`.
2. **Trailing Bytes Check**: Added a final check to ensure no bytes remain after processing all records. If bytes remain, the program exits with `error: trailing bytes`.

## Verification

- **Regression Tests**: Created tests for both valid archives (pass with `valid archive`) and malformed archives (fail with `error: truncated archive`).
- **Smoke Tests**: Ensured existing valid archives still produce the same output as before the fix.
- **Sanitizer Builds**: Confirmed no AddressSanitizer/UBSan errors with malformed inputs.

## Conclusion

The fixed program now correctly rejects malformed archives with the documented error behavior while preserving the original output for valid archives. Regression tests ensure the fix is durable against future changes.