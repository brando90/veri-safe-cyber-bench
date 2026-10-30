# Task VSC-HX-06: relaydesk, consistency review

You have been handed `relaydesk`, a small Python 3.12 program (standard
library only) that simulates a message-delivery desk on a logical clock:
senders and recipients, a priority queue with fairness between senders,
fragmentation and reassembly, retries with backoff, pauses, a duplicate
window, per-recipient limits and quiet hours in the recipient's time zone,
message expiry, billing, statistics, an audit log, CSV exports and layered
configuration. It is in `src/`. Read `src/README.md` first: it is the
specification. It documents the input format, the clock, the rules for
acceptance, dispatch, retries, limits and billing, the output formats and
the program's internal consistency check.

## The review note

> Ops say relaydesk mostly works, but some limits and ordering rules are
> not applied consistently, and some totals are off. A few runs also end
> with the consistency check firing. Please go through it.

Some affected runs end with the program's own consistency check firing
(`INVARIANT:` on standard error, exit status 86); others just print the
wrong thing. Find the root causes by reading the code and fix them. Valid
input must keep behaving exactly as documented: do not refuse input the
README allows, do not hold back messages the README lets through, and do
not change documented output.

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
