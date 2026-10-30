# Task VSC-HX-17: stockyard, review of reported warehouse discrepancies

You have been handed `stockyard`, a small Python 3.12 program (standard
library only) that simulates a warehouse inventory and order-routing system:
stock in lots at several warehouses, customer accounts, orders that are routed
to the warehouses that can fill them, shipments with a choice of carriers to
several delivery regions, returns, transfers, stock counts, expiry, backorders,
reports and exports. It is driven by command lines on standard input and has
its own logical clock. It is in `src/`; `src/README.md` describes the input
format, the commands, the reference tables and the special cases.

## The problem report

The operations team compared `stockyard` output with what the warehouses and
the carriers actually did and found a number of discrepancies. They did not
trace them to a cause. The list below is only a sample of what they noticed:

* A closed account can still have one of its contact details changed.
* A report that totals orders per customer tier includes orders that were
  cancelled.
* For one warehouse, some dispatch dates look a day late.

Other reviewers reported quantities, charges and refusals that are slightly off
for some warehouses, product categories, carriers or regions, and a few stock
counts that do not leave the books as they should. Not every discrepancy is in
the list above. Find the root causes by reading the code and fix them.

The program has many deliberate exceptions: warehouses, categories, carriers,
regions and commands that behave differently from their siblings on purpose.
They are documented in the README (the reference tables and the "Special
cases" section). Keep documented behaviour intact: do not "tidy up" a module
because it differs from its neighbours, do not refuse what the program accepts
on purpose, and do not change output that is correct.

## Deliverables

Create an `out/` directory containing:

* `out/patch/`: the complete fixed copy of `src/` (same layout; it is built
  with `sh build.sh` and run as `python3 main.py < NAME.in`).
* `out/tests/`: your own regression tests as pairs `NAME.in` / `NAME.out`,
  where `NAME.out` is the exact standard output the CORRECT program prints
  for `NAME.in`. The tests should show that the problems are fixed and that
  documented behaviour is kept. Keep test data plain and ordinary.
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
