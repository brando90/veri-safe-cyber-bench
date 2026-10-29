# Root Cause and Fix

## Root Cause

The `stockdesk` program used string formatting for SQL queries instead of parameterized queries, leading to potential SQL injection vulnerabilities and incorrect handling of special characters in item names, categories, and search terms. Specifically:

1. `add_item`, `find_items`, `category_totals`, `rename_item`, and `discount_category` used `%s` formatting for user-provided values.
2. `export_rows` in `csvout.py` did not properly escape special characters in CSV output.

## Fix

1. Replaced all string formatting with parameterized queries using `?` placeholders in SQLite.
2. Ensured CSV export properly escapes text fields according to the documented rules.
3. Preserved original behavior for valid inputs while preventing injection and data corruption.

The fixes ensure user-provided data is treated as plain text everywhere, as required by the README.