# slotbook Fixes

## Authorization Issues

**Root Cause:** Some command handlers did not check operation-specific permissions beyond the command's listed permissions.

**Fix:** Added permission checks for all operations within handlers (e.g., `customer-archive` now checks both `customer.write` and `appt.cancel`).

## Data Handling

**Root Cause:** Direct string interpolation in SQL queries risked injection and incorrect data handling.

**Fix:** Replaced all SQL queries with parameterized statements. Ensured output formats (CSV/TSV/audit) use proper escaping per README.

## Money Rules

**Root Cause:** Totals were calculated before per-line rounding, leading to incorrect figures.

**Fix:** Rounding now applied per line before summation. Reports use rounded values. Used `money.py` for consistent calculations.

## Consistency

All fixes preserve documented behavior. Smoke tests pass. New tests in `out/tests/` verify fixes.