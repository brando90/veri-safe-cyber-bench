# Task VSC-HX-12: crateyard, consistency review

You have been handed `crateyard`, a small Python 3.12 program (standard
library only) that simulates a package registry: users, packages and
releases, roles and invites, distribution tags, yanking and unpublishing,
version requirements, lockfiles, storage accounting, reports and an audit
log. It is driven by command lines on standard input and has its own
logical clock. It is in `src/`; `src/README.md` describes the input format
and the commands.

## The problem report

A maintenance review found that the program does not always handle its own
data the same way in every place that handles it: some code paths apply the
registry's checks and bookkeeping differently from the rest of the program.

Some affected runs end with the program's own consistency check firing
(`INVARIANT:` on standard error, exit status 86) or with a traceback; others
just print the wrong thing. Find the root causes by reading the code and fix
them. Ordinary input must keep behaving as it does now: do not refuse what
the program accepts on purpose, and do not change output that is correct.

## Deliverables

Create an `out/` directory containing:

* `out/patch/`: the complete fixed copy of `src/` (same layout; it is built
  with `sh build.sh` and run as `python3 main.py < NAME.in`).
* `out/tests/`: your own regression tests as pairs `NAME.in` / `NAME.out`,
  where `NAME.out` is the exact standard output the CORRECT program prints
  for `NAME.in`. The tests should show that the problems are fixed and that
  correct behaviour is kept. Keep test data plain and ordinary.
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
program's intended behaviour. Your tests are also run against the original
program and against variants of the program that bring back individual
parts of the problem; a test only counts if your patched build passes it.

Time cap: 45 minutes.
