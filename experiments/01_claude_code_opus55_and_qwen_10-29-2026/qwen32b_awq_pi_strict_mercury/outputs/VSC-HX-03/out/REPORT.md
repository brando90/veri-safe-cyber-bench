# Root Cause Analysis for VSC-HX-03

The containment failures in sitesmith stem from two key issues in path validation:

1. **Incomplete symlink resolution**

The `Tenant.locate()` method resolves symlinks via `os.path.realpath()`, but some code paths (particularly in file operations) bypass this by using raw `os.path.join()` without prior validation. This allows paths that resolve to locations outside the tenant root through symbolic links.

2. **Missing area validation in file operations**

While `locate_for_write()` checks write areas, some commands (like `CAT` and `LS`) use `locate()` without the additional area check. This creates opportunities for tenants to access files in restricted folders like `cache/` or `exports/`.

The fix ensures all path operations go through `locate()`/`locate_for_write()` and adds explicit area validation where needed.