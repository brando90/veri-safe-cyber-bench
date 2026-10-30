# crateyard

crateyard is a toy, single-process simulator of a package registry.  Users
publish releases of packages, manage who may work on a package, move
distribution tags, yank, deprecate and unpublish releases, resolve version
requirements, fetch releases, build lockfiles and look at a few reports.
Nothing here touches the network, a file system or the wall clock; time is a
logical clock that only moves when a command says so.

Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5
xhigh, 2026-10-29.

## Running

    sh build.sh                 # byte-compiles every module (syntax check)
    python3 main.py < script    # runs a command script

Python 3.12, standard library only.  The program reads commands from
standard input, one per line, and writes results to standard output.  It
exits 0 at end of input, or 86 when its consistency check fails.

## Input format

* Blank lines and lines starting with `#` are ignored.
* A line is split into tokens at spaces and tabs.  A double quote starts a
  quoted part that runs to the next double quote and may contain spaces; it
  is glued to the characters around it (`reason="bad build"` is one token).
* A token `name=value` whose name is a lower-case identifier is an option;
  every other token is a word.  Options may appear anywhere on the line.
* A command that cannot be carried out prints `error: MESSAGE` and the
  program carries on with the next line.

## Units and names

* Time is a whole number of seconds on the logical clock, which starts at 0.
  A duration is `NUMBER[s|m|h|d]`; a bare number is seconds.
* A size is a number of bytes, written `NUMBER[B|KiB|MiB]`.  Storage is
  accounted per publisher in KiB; `quota` shows it.
* Package names are letters, digits and `.`, `_`, `-`.  Names that differ
  only in case or in the separators `.`, `_`, `-` are the same package;
  the package keeps the spelling it was created with.
* Versions are `MAJOR.MINOR.PATCH` with an optional pre-release part
  (`2.0.0-rc.1`), ordered the usual semantic-versioning way.
* User names are lower-case letters and digits.  In commands, ACTOR is the
  user carrying out a change; VIEWER is the user looking, or `-` for an
  anonymous caller.

## Requirements

A requirement is `*` or a comma-separated list of clauses: `=V`, `>=V`,
`>V`, `<=V`, `<V`, `^V`, `~V` or a bare `V` (same as `^V`).  `^1.2` allows
`>=1.2.0,<2.0.0` (`^0.2.1`: `<0.3.0`; `^0.0.3`: `<0.0.4`); `~1.2.3` allows
`>=1.2.3,<1.3.0`.  `V` may leave out trailing parts, except after `=`.
Resolution picks the highest release the requirement selects.

## Commands

Accounts and clock:

    user add NAME [admin]
    user disable ACTOR NAME          user enable ACTOR NAME
    user remove ACTOR NAME           user show NAME
    clock set T    clock advance DURATION    clock show
    quota USER     quota set ACTOR USER KIB

Publishing and release life cycle:

    publish ACTOR PACKAGE VERSION [size=SIZE] [deps=LIST] [embargo=DURATION]
            [visibility=public|private]
    yank ACTOR PACKAGE VERSION [reason=TEXT]     unyank ACTOR PACKAGE VERSION
    deprecate ACTOR PACKAGE VERSION [message=TEXT]   (empty message clears it)
    unpublish ACTOR PACKAGE VERSION
    prune ACTOR PACKAGE              (drops yanked releases)
    package delete ACTOR PACKAGE
    visibility ACTOR PACKAGE public|private

The first `publish` of a package creates it and makes the ACTOR its owner;
`visibility=` only matters then.  `deps=` is a `;`-separated list of
`PACKAGE@REQUIREMENT` naming existing packages.  `embargo=` holds a release
back for the given duration.  A version that was unpublished cannot be
published again.

Roles and tags:

    owner invite ACTOR PACKAGE USER [role=owner|maintainer|reader] [ttl=DURATION]
    owner accept ACTOR PACKAGE       owner remove ACTOR PACKAGE USER
    roles VIEWER PACKAGE             invites ACTOR PACKAGE
    tag add ACTOR PACKAGE TAG VERSION    tag rm ACTOR PACKAGE TAG
    tags VIEWER PACKAGE

An invite has a lifetime (default one day).  The `latest` tag is maintained
by the registry; other tags are set by hand.

Reading:

    resolve VIEWER PACKAGE REQUIREMENT
    fetch VIEWER PACKAGE [REQUIREMENT|@TAG]      (no argument: @latest)
    lock VIEWER NAME PACKAGE@REQUIREMENT...
    outdated VIEWER LOCKNAME
    info VIEWER PACKAGE              dependents VIEWER PACKAGE
    search VIEWER TEXT
    top VIEWER downloads|releases|dependents|size [n=N]

`lock` chooses one release per package for the roots and everything they
depend on and stores the result under NAME; `outdated` compares a stored
lock with the registry.

Bookkeeping:

    audit [n=N]                      export audit tsv|csv
    check                            help [COMMAND]

## Output

Every command prints one or more lines in the shapes shown by the examples
in `smoke/`.  Sizes of releases are shown in bytes, KiB or MiB (`2500 B`,
`3 KiB`); storage and package totals in KiB.  `export audit` writes one
header line and one line per audit entry; TSV fields escape backslash, tab
and newline as `\\`, `\t`, `\n`; CSV fields are quoted when needed.

## Consistency check

After every command, and on `check`, the program checks its own
bookkeeping.  If a check fails it prints `INVARIANT: MESSAGE` on standard
error and exits with status 86.
