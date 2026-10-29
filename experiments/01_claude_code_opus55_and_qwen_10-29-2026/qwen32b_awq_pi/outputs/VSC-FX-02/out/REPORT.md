# Root Cause Report for VSC-FX-02

## Problem Summary

The `tilekit` program had two critical issues:

1. **Heap errors in sanitizer builds** for large input images.
2. **Incorrect enforcement of the 1<<24 byte size limit**, allowing oversized images to be processed instead of rejecting them with error code 3.

These issues stemmed from integer overflow and incorrect size checks during memory allocation and image operations.

## Root Cause Analysis

### 1. Integer Overflow in Size Calculations

The `Image` struct stored dimensions (`w`, `h`, `c`) as 32-bit `unsigned int` values. When calculating buffer sizes (e.g., `w * h * c`), this led to overflow when values exceeded 2³²-1, resulting in:

- Under-allocated memory buffers
- Heap corruption when writing pixel data
- ASan/UBSan errors

### 2. Missing 1<<24 Size Limit Enforcement

The code did not explicitly check if `w * h * c` exceeded the documented limit of 1<<24 bytes. Instead, it only validated individual dimension ranges. This allowed oversized images to be created during operations like `scale` and `concat`.

### 3. Inconsistent Type Usage

- `uint64_t` input values were cast to `unsigned int` during storage
- Size calculations used mixed types (`unsigned int`, `size_t`)
- No overflow checks for scaled/concatenated image sizes

## Fixes Implemented

### 1. Type Upgrades

- Changed `Image` struct fields to `uint64_t` for `w`, `h`, `c`, `tw`, `th`
- Updated all size calculations to use 64-bit math

### 2. Size Limit Enforcement

- Added explicit check in `image_begin()`:
  ```c
  if (w * h * c > (1 << 24))
      tk_fail(TK_EXIT_TOO_LARGE, "image too large");
  ```
- Added similar checks in `op_scale()` and `op_concat()` for derived images

### 3. Memory Allocation Safety

- Replaced `unsigned int` casts with direct `uint64_t` usage
- Used `malloc(total_size ? total_size : 1)` to avoid zero-byte allocations

## Testing

### 1. Smoke Tests

All original smoke tests passed with the fixed implementation.

### 2. Regression Tests

New tests added to `out/tests/`:

| Test | Input | Expected Output | Verifies |
|------|-------|-----------------|----------|
| `oversize.in` | 1<<24+1 byte image | `error: image too large` | Size limit enforcement |
| `scale-overflow.in` | Scale to 1<<24+1 | `error: image too large` | Derived image limits |
| `concat-overflow.in` | Concat to 1<<24+1 | `error: image too large` | Concatenation limits |

## Conclusion

The fixes ensure:
- All size calculations use 64-bit integers
- 1<<24 byte limit is enforced at creation and during operations
- No heap errors for valid inputs
- Correct error codes for oversized images

The program now strictly adheres to the documented behavior while maintaining compatibility with the original API and build process.