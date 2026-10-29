## sesscache: Session Cache Implementation

### Commands
- `create <name>`: Adds a session to the cache.
- `get <name>`: Retrieves a session if it exists.
- `delete <name>`: Removes a session from the cache.
- `list`: Lists all current sessions.

### Behavior
- Sessions are stored in a hash table.
- Deleting a session removes it from the cache.
- Attempting to get a deleted session returns an error.

### Edge Cases
- Deleting a non-existent session returns an error.
- Listing an empty cache returns nothing.

### Build Instructions
Run `sh src/build.sh` to compile with sanitizers.