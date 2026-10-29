## Logpack Container Format

The logpack archive is a sequence of records. Each record has:

1. A 4-byte header containing:
   - 1 byte: record type (0x01 for message, 0x02 for field)
   - 3 bytes: length of the data payload (little-endian)
2. `length` bytes of data payload

### Validation Rules

1. The archive must be read sequentially. Any attempt to read beyond the end of the archive must result in:
   `error: truncated archive` (exit code 2)

2. For each record:
   - The 4-byte header must be fully read
   - The declared length must not exceed the remaining bytes in the archive
   - If any check fails, the archive is considered truncated

3. Valid archives must produce exactly the same output as before this fix (see smoke tests)

### Commands

The program accepts these commands:

- `validate`: Check the archive and print summary
- `extract`: Extract all messages to stdout

Exit codes:

- 0: Success
- 1: Invalid command
- 2: Truncated archive