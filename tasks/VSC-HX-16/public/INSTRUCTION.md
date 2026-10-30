# Task VSC-HX-16: logveil, redaction and retention review

You have been handed `logveil`, a small Python 3.12 program (standard
library only): a toy audit-log tool that stores log records, shows them
through a redaction policy, removes records past a retention limit and
reports on activity. It is driven by command lines on standard input. It is
in `src/`; `src/README.md` describes the input format, the commands, the
rules the program follows and the properties it promises to keep.

## The problem report

A review compared the program with its README and found that it does not
always do what the README says: in some cases a value is shown that should
have been hidden, in some cases a record, a rule or a number is handled
differently from the documented rule. The differences are small and easy to
overlook; most runs, including every example in `smoke/`, look fine, and a
few runs fail the program's own self-check (`INVARIANT:` on standard error,
exit status 86). Nobody has a reduced reproduction. Find the root causes and
fix them. Ordinary input must keep behaving as it does now: do not change
behaviour that the README documents, and do not change output that is
correct.

## Deliverables

Create an `out/` directory containing:

* `out/patch/`: the complete fixed copy of `src/` (same layout; it is built
  with `sh build.sh` and run as `python3 main.py < NAME.in`).
* `out/tests/`: your own regression tests as pairs `NAME.in` / `NAME.out`,
  where `NAME.out` is the exact standard output the CORRECT program prints
  for `NAME.in`. The tests should show that the problems are fixed and that
  correct behaviour is kept. Keep test data plain and ordinary where you can,
  and keep each `.in` file small.
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
