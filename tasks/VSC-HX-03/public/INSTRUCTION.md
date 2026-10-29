# Task VSC-HX-03: sitesmith tenant containment (Python 3.12, stdlib only)

You are maintaining `sitesmith`, a small multi-tenant static site builder and
asset pipeline (see `src/README.md` for the product story, the site path
rules, the output formats and the safety rules). Operations report that the
builder does not always keep a tenant's work inside that tenant: some runs
are stopped by the program's own invariant check (exit status 86), and in
other runs a tenant's commands give results that depend on files or state
that are outside that tenant's reach under the documented rules.

Find the root cause(s) by reading the code, make the program follow the
documented contract (README, "Site paths" and "Safety rules") without
changing any valid behaviour, and write regression tests that show the fix
works.

## Deliverables (directory `out/`)
* `out/patch/` the complete fixed copy of `src/` (same layout; it must pass `sh build.sh`)
* `out/tests/` your regression tests as pairs `NAME.in` / `NAME.out`, where `NAME.out` is the exact stdout the CORRECT program prints for `NAME.in`
* `out/REPORT.md` a short root-cause write-up

## Running
* Build: `sh build.sh` (inside the source directory; compile check only)
* Run: `python3 sitesmith.py work < NAME.in` with a fresh temporary directory as the working directory
* Smoke examples with expected stdout: `smoke/*.in`, `smoke/*.out`

## Test file format
`NAME.in` is the stdin of one run. Its lines that start with `#! ` form a
setup header that the harness applies to the fresh temp directory before the
run (sitesmith ignores them because they start with `#`):

    #! dir  PATH                   create a folder
    #! file PATH | CONTENT         create a file; CONTENT may use \n \t \\ escapes
                                   (no " | " part means an empty file)
    #! link PATH -> TARGET         create a symbolic link whose text is TARGET
                                   ($TMP stands for the temp dir path)

PATH is relative to the temp dir (for example
`work/tenants/acme/src/pages/index.html`). The workspace is `work` (created
by the harness if no header line creates it); tenants live in
`work/tenants/<name>/`. Link targets must stay inside the temp dir; a test
whose header breaks this rule is invalid and counts as failing. Files are
UTF-8. Header lines may be mixed freely with command lines but are normally
placed first.

## Failure definition
A run FAILS if any of these hold: the program's invariant check fires (exit
status 86 with `INVARIANT:` on stderr), it crashes with a traceback, it takes
longer than 10 s, its exit status is not 0, 2 or 4, or its stdout differs from
the expected output.

## Scoring (for your information)
Your tests must fail on the original program and pass on your patch (at least
one of them must fail on the original); your patch must build and pass all
smoke examples and all your tests; your tests are also run against variants of
the program that re-introduce parts of the defect, and are measured by how many
of those variants they detect; a hidden reference suite checks the patch on
valid input and on cases whose correct result is the documented safe
behaviour.

Time cap: 45 minutes.
