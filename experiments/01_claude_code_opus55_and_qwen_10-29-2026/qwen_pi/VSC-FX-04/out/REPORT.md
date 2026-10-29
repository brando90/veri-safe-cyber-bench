## Root Cause Analysis

The defect stemmed from improper reference count management in `delete_session()`. The original code immediately freed sessions upon deletion without checking if they were still referenced elsewhere (e.g., via `get`). This allowed:

1. Double-free: If a session was deleted while still referenced
2. Use-after-free: If a session was accessed after deletion

### Fix
Modified `delete_session()` to:
- Decrement the session's reference count
- Only free memory when refcount reaches 0
- Added explicit tracking of refcount changes

This ensures sessions are only destroyed when all references are explicitly released.