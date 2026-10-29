# Root Cause Analysis for VSC-FX-03

The containment check vulnerabilities in docvault stem from three core issues:

1. **Text-based containment checks** in `Session._locate_file()` use `vpaths.within_text()` which only validates path strings without resolving symbolic links or normalizing paths. This allows attackers to bypass checks using `../` sequences that appear harmless in string form but resolve outside the user directory.

2. **Incomplete symlink resolution** in `cmd_export()`: while it resolves paths with `vpaths.resolve_real()`, it doesn't re-verify containment after symlink expansion. This creates a window where resolved paths could escape the user's directory.

3. **Inconsistent alias handling**: alias expansion in `aliases.AliasTable.expand()` operates on raw path strings before containment checks, allowing malicious aliases to construct bypass paths that only fail after multiple expansion steps.

The fix requires converting all containment checks to operate on resolved real paths using `os.path.realpath()` and `vpaths.within_real()` for final validation.