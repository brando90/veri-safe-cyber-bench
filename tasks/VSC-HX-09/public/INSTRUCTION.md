# Task VSC-HX-09: policyforge maintenance review

You have been handed `policyforge`, a small Python 3.12 access-policy engine
(standard library only): policy sets and rules with conditions in a small
expression language, decisions and a decision log, approvals with expiry,
reports in several formats, secret redaction and policy bundles. It is in
`src/`. Read `src/README.md` first: it is the specification, including the
general rules that hold for every command and the program's internal
consistency check.

## The review note

A review found that the program does not always follow its own general
rules: input is not always treated purely as data on its way to the output,
and some limits and conventions are not applied consistently. Some affected
runs end with the program's consistency check firing (`INVARIANT:` on
standard error, exit status 86); others just print something different from
what the README specifies.

Find the root causes by reading the code and fix them. Valid input must keep
behaving exactly as documented: do not refuse what the README allows and do
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
