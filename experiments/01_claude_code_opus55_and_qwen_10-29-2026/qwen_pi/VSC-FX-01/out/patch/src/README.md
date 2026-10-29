## logpack

A synthetic tool to validate binary log-record archives.

### Container Format

Each archive starts with a 4-byte magic number (`0xdeadbeef`), followed by records. Each record has:
- 4-byte length (little-endian)
- N bytes of payload (N is the length)

### Commands

- `validate`: Check archive integrity

### Error Handling

- `error: truncated archive` (exit 2) if declared length exceeds available bytes.