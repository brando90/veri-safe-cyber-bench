# Root Cause Report for VSC-FX-03

## Problem Summary
The containment check in `docvault` allowed paths to resolve outside the user's root directory in three scenarios:
1. **Unresolved path checks** - Text-based checks (`str.startswith`) allowed `..` and symlinks to bypass containment
2. **Alias expansion** - Alias targets weren't re-validated after expansion
3. **Export path expansion** - Recursive directory expansion didn't re-validate paths after expansion

## Root Causes
1. **Text-based containment check**: The original implementation used `str.startswith` on unresolved paths (e.g., `joined = vpaths.join_user(user_root, rel)` followed by `within_text(user_root, joined)`). This allowed paths like `malicious/../vault_root_symlink` to pass checks before resolution.

2. **Incomplete alias validation**: While alias targets were validated at definition time, subsequent expansions didn't re-validate the final resolved path.

3. **Missing post-expansion checks**: The `archive.collect()` function expanded directories recursively but didn't re-validate each new path after expansion, allowing potential escape paths to be included in exports.

## Fixes Implemented
1. **Path resolution enforcement**: Replaced all text-based checks with `vpaths.resolve_real()` which:
   - Resolves all symlinks with `os.path.realpath`
   - Uses `os.path.commonpath([user_root, real]) == user_root` for containment checks
   - Raises `Denied()` for paths outside the user root

2. **Alias expansion hardening**: All alias-expanded paths now go through `vpaths.resolve_real()` before use.

3. **Export path re-validation**: Added `vpaths.resolve_real()` checks during directory expansion in `archive.collect()`, ensuring:
   - Every new path is validated against the user root
   - Symlinks and nested paths are properly resolved
   - The exports directory itself is excluded

## Verification
- **Regression test**: `escape_attempt.in` demonstrates a symlink-based escape attempt that is now denied
- **Smoke tests**: All original smoke tests pass with no behavioral changes
- **Security coverage**: The fixes handle all documented safe behaviors and edge cases involving:
  - Symlinks
  - `..` path components
  - Nested directory expansions
  - Alias chains

The implementation now ensures containment checks are applied consistently across all operations, resolving paths fully before any validation.