# Root Cause Analysis and Fixes for VSC-FX-05

## Root Causes

1. **String formatting in SQL queries**
   - `add_item()`: Used `%s` formatting for all fields, vulnerable to SQL injection and special characters
   - `find_items()`: Manually constructed `LIKE '%%%s%%'` pattern
   - `category_totals()`: Appended `WHERE category = '%s'` with string interpolation
   - `rename_item()`: Used string formatting with legacy `_clean()` function
   - `discount_category()`: Used `%s` for category parameter

2. **Legacy cleanup function**
   - `_clean()` stripped quotes and split on semicolons, altering user input

## Fixes Applied

1. **Parameterized all SQL queries**
   - Replaced string formatting with `?` placeholders and parameter tuples
   - Example: `VALUES (?, ?, ?)` with `(sku, category, name)` tuple
   - For `LIKE` patterns, constructed `f"%{text}%"` separately and passed as parameter

2. **Removed legacy cleanup**
   - Deleted `_clean()` function
   - Directly passed user input to SQL parameters without modification

3. **Fixed discount query**
   - Added `?` placeholder for percentage calculation

## Validation

- All special characters (`, ;, %, _) are now handled correctly
- Input is stored verbatim as documented
- Maintained original behavior for normal inputs
- Added parameterized queries in 5 locations
- Removed data-altering function