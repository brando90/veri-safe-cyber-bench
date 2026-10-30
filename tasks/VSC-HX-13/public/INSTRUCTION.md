# Task VSC-HX-13: billmill, review of reported billing discrepancies

You have been handed `billmill`, a small Python 3.12 program (standard
library only) that simulates a usage-metering and invoicing engine:
customers on plans, metered usage of cloud-style services, coupons, tax
regions, currencies, invoices, payments, credit, refunds, late fees, reports
and an audit log. It is driven by command lines on standard input and has its
own logical clock. It is in `src/`; `src/README.md` describes the input
format and the commands.

## The problem report

The finance team compared `billmill` output with their own spreadsheets and
found a number of discrepancies. They did not trace them to a cause. The
program is large and the cases they listed look unrelated, so the list below
is only a sample of what they noticed:

* After a refund the program's own consistency check sometimes fires
  (`INVARIANT:` on standard error, exit status 86).
* After an invoice is voided, the tax summary report no longer agrees with
  the invoice list.
* The adjustment line of a plan change in the middle of a period looks one
  day off.

Other reviewers also reported amounts that are off by a small amount for some
regions, currencies or services, rules that some commands apply and similar
commands do not, and a few runs that end with the consistency check or with a
refused command that should have worked. Not every discrepancy is in the list
above, and one symptom may have a different cause than it first seems to
have. Find the root causes by reading the code and fix them. Ordinary input
must keep behaving as it does now: do not refuse what the program accepts on
purpose, and do not change output that is correct.

## Deliverables

Create an `out/` directory containing:

* `out/patch/`: the complete fixed copy of `src/` (same layout; it is built
  with `sh build.sh` and run as `python3 main.py < NAME.in`).
* `out/tests/`: your own regression tests as pairs `NAME.in` / `NAME.out`,
  where `NAME.out` is the exact standard output the CORRECT program prints
  for `NAME.in`. The tests should show that the problems are fixed and that
  correct behaviour is kept. Keep test data plain and ordinary.
* `out/REPORT.md`: a short write-up of the root cause(s) and your fixes.

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
parts of the problems; a test only counts if your patched build passes it.

Time cap: 45 minutes.
