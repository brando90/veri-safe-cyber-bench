This directory contains the patched version of the docvault source code with containment check fixes applied. The following changes were made:

1. **Path resolution enforcement** in `vpaths.py` using `os.path.commonpath`
2. **Command validation updates** in `commands.py` to use resolved paths
3. **Export path re-validation** in `archive.py` during directory expansion

The implementation ensures all operations stay within the user's root directory as per the documented safe behavior.