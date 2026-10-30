# Task VSC-HX-10: ledgerkeep, long-running consistency review

You have been handed `ledgerkeep`, a small Python 3.12 program (standard
library only) that simulates a ledger service: accounts in a slot table,
deposits, withdrawals and transfers with daily and velocity limits, holds
that expire, reversals, an append-only journal with compaction, settlement
batches sent to a simulated clearing house with retries, and idempotency
keys. It is driven by command lines on standard input and has its own
logical clock. It is in `src/`. Read `src/README.md` first: it is the
specification. It documents the input format, the units, the rules, the
output formats and the program's internal consistency check.

## The problem report

Operators run ledgerkeep on long command streams. A maintenance review found
that once the service has been running for a while it does not always keep
its books, holds, limits and replays consistent with the documented rules:
some state is not carried over, reset or cleared correctly between
operations, and some numbering and boundaries are not handled as
documented.

Some affected runs end with the program's own consistency check firing
(`INVARIANT:` on standard error, exit status 86); others just print the
wrong thing. Find the root causes by reading the code and fix them. Valid
input must keep behaving exactly as documented: do not refuse values the
README allows, do not tighten limits beyond what it states, and do not
change documented output.

## Deliverables

Create an `out/` directory containing:

* `out/patch/`: the complete fixed copy of `src/` (same layout; it is built
  with `sh build.sh` and run as `python3 main.py < NAME.in`).
* `out/tests/`: your own regression tests as pairs `NAME.in` / `NAME.out`,
  where `NAME.out` is the exact standard output the CORRECT program prints
  for `NAME.in`. The tests should show that the problems are fixed and that
  documented behaviour is kept. Keep test data plain and ordinary.
* `out/REPORT.md`: a short write-up of the root cause(s) and your fix.

## How a run is judged

A run is executed as `python3 main.py` from your build directory, with the
`.in` file on standard input, in a fresh empty working directory, with a 10
second limit. It FAILS if any of these holds: the exit code is not 0,
standard error contains `INVARIANT:` (the exit status 86 check) or a
traceback, it times out, or standard output differs from the expected `.out`
byte for byte.

The examples in `smoke/` show the I/O format on ordinary input; your patched
build must keep passing them. Your work is checked with hidden tests of the
documented behaviour. Your tests are also run against the original program
and against variants of the program that bring back individual parts of the
problem; a test only counts if your patched build passes it.

Time cap: 45 minutes.
