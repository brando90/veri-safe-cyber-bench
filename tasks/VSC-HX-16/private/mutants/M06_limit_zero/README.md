# logveil

A toy audit-log redaction and retention tool. It keeps a table of log records
in memory, applies a redaction policy when records are exported, removes
records that are older than a retention limit, and reports on activity per
source and per user. It is a synthetic program for a maintenance exercise: all
names, secrets and tokens in examples are made up.

Python 3.12, standard library only. Build with `sh build.sh` (it only
byte-compiles). Run with `python3 main.py < commands.txt`.

## Input

One command per line. Blank lines and lines starting with `#` are ignored.
Output goes to standard output. A refused command prints `error: MESSAGE` and
the run goes on. A log line that is not stored prints `rejected: REASON`.

| Command | Effect |
|---|---|
| `now TIMESTAMP` | set the clock (default `2026-01-01T00:00:00Z`) |
| `retain DAYS` | retention limit in days (default 30) |
| `window SECONDS` | activity window for alerts (default 60, at least 1) |
| `limit SOURCE COUNT` / `limit * COUNT` | alert limit of one source / of every source without its own (default 20) |
| `top COUNT` | rows in the by-user table (default 3, at least 1) |
| `salt TEXT` | salt for pseudonyms (the rest of the line) |
| `strict on` / `strict off` | strict mode (default off) |
| `rule ACTION NAME` | ACTION is `redact`, `mask`, `drop`, `pseudo` or `keep` |
| `rule prefix PREFIX [ACTION]` | the action (default `redact`) applies to every field whose name starts with PREFIX |
| `unrule NAME` | remove every rule for NAME (and prefix rules with that prefix) |
| `log TIMESTAMP SOURCE USER [NAME=VALUE ...] [-- MESSAGE]` | store a record |
| `purge` | apply retention |
| `export [SOURCE] [keep=NAME,NAME]` | print the records (of one source) as the policy shows them |
| `show ID` | print one record as the policy shows it |
| `report` / `days` / `stats` / `rules` | summaries |
| `check` | run the self-check and print `check ok` |
| `help` | list the commands |

Numbers are plain decimal digits. `limit` may be 0.

## Timestamps

A timestamp is `YYYY-MM-DDTHH:MM:SS` followed by `Z`, an offset such as
`+0200` or `-0530`, or nothing (taken as UTC). Records and the clock are
compared and printed in UTC (`...Z`). Daily summaries use UTC days.

## Records

A record has a timestamp, a source (letters, digits, `.`, `_`, `-`; folded to
lower case), a user (any word) and fields. A field is `NAME=VALUE`: the name
is everything before the first `=` and is folded to lower case; the value is
the rest of the word and may itself contain `=`. A repeated name keeps the
last value. A `bytes` field must be digits (empty counts as 0), otherwise the
line is rejected with `rejected: bad bytes`. A message follows ` -- ` and runs
to the end of the line. Records get ids 1, 2, ... in the order they are
accepted.

An exported record is printed as
`#ID TIMESTAMP SOURCE USER NAME=VALUE ... -- MESSAGE` with the fields in name
order. Messages longer than 80 characters are cut to 77 characters followed
by `...`. When fields were changed by the policy a second line lists their
names in name order.

## Redaction policy

Field names are matched case-insensitively and a single leading `x-` is
ignored, so `X-Auth` and `auth` are the same field. Rules and prefix rules use
the same matching. The action for a field:

* `drop` removes the field, `redact` replaces the value with `[redacted]`,
  `pseudo` replaces it with `p-` and eight hex digits derived from the salt
  and the value, `mask` keeps only the last quarter of the characters (the
  length divided by four, rounded down) visible and replaces every other
  character with `*`; a value shorter than 4 characters is masked completely.
* When several explicit rules or prefix rules match, the strongest wins: drop,
  then redact, then pseudo, then mask. Every prefix rule that was added counts.
* In strict mode a field with no explicit rule is redacted unless a `keep`
  rule names it. Explicit rules win over `keep`. `keep` does nothing outside
  strict mode.
* `export ... keep=a,b` treats `a` and `b` as if they had `keep` rules for
  that one export only; it never changes the policy.
* The text of a message is scrubbed on export: a word `password=`, `passwd=`,
  `secret=`, `token=` or `apikey=` (any letter case) followed by a value has
  the value masked like `mask`, for every occurrence in the message, and every
  `tok_` followed by at least 8 letters or digits is masked like `mask`.
  Scrubbing happens before a long message is cut.
* Exporting never changes the stored records.

## Retention

`purge` removes every record that is more than the retention limit old at the
current clock (a record exactly that old is kept; a record dated after the
clock is kept) and prints `purged N records (ids ...), K kept`, or
`purged 0 records, K kept`. Ids of removed records are listed in order.

## Activity and alerts

The window of a source at time t holds its records with times after
t minus the window length, up to and including t. A source raises an alert
when some window holds more records than its limit (a source with limit 0
alerts on any record). A source whose busiest window holds exactly its limit
is listed as `at limit`.

## Reports

`report` prints the clock, record and byte totals, the number of sources and
the average records per source (rounded to the nearest whole number, halves to
the even number, as Python's `round` does), the tables by source, by user (the
first `top` rows), by domain (the part of the user after the last `@`, `-` when
there is none) and by level (severity order error, warn, info, debug, then
others; a record without a `level` field counts as `info`), the largest record
(the lowest id when equal), the alerts, and the records dated after the clock
with the days ahead rounded up.

Tables list the highest count first and equal counts in name order. A share is
a percentage of the record total with one decimal, halves rounded up. `stats`
counts how many records carry each field by normalised name. `days` lists the
UTC days that have records, oldest first.

## Self-check

After every command the program checks these properties and, if one fails,
prints `INVARIANT: MESSAGE` on standard error and exits with status 86:

* ids are strictly increasing;
* a stored record is unchanged since it was logged;
* after a purge no record that was present is older than the retention limit
  that was in force.
