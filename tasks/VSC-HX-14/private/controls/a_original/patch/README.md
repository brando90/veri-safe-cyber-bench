# eventlane

A toy calendar and recurrence engine. It keeps a table of events (a title, a
start, a length, an optional recurrence rule, a UTC offset, a priority,
categories and skipped dates), answers questions about them (occurrences,
agenda, busy time) and converts dates, offsets, durations and references. It
also writes the events out in a text form and in a checksummed binary pack
form and reads both back.

Python 3.12, standard library only. Build with `sh build.sh` (it only
byte-compiles). Run with `python3 main.py < commands.txt`. The program has its
own calendar arithmetic; it does not use `datetime`.

## Input

One command per line. Blank lines and lines starting with `#` are ignored.
A line is split into words at blanks; a double quote starts a quoted part that
runs to the next double quote (it may contain blanks). A word `name=value`
with a lower-case `name` is an option (an unquoted title that contains `=`
must be quoted). Output goes to standard output; a refused command prints
`error: MESSAGE` and the run goes on.

## Dates, instants and offsets

* A date is `YYYY-MM-DD`, years 1 to 9999 (proleptic Gregorian). Day numbers
  count days from 1970-01-01 (day 0). Weeks begin on Monday.
* A start is `YYYY-MM-DDTHH:MM` or `YYYY-MM-DDTHH:MM:SS` (local time), or just
  a date for an all-day event. Stored starts have minute resolution: a start
  given with seconds moves to the nearest minute, half a minute rounding up,
  and the move may carry into the hour, the day, the month and the year.
* An offset is `Z`, `+HH:MM`, `-HH:MM`, `+HHMM` or `+HH`, from -12:00 to
  +14:00. It is written `+HH:MM`. All-day events are floating: their offset is
  stored but never applied.
* A duration is parts in descending order (`1d2h3m4s`) or one decimal part
  (`1.5h`, up to six decimals, rounded to whole seconds with halves up). The
  longest duration is 400d.

## Events

`event add ID TITLE START [dur=D] [rule=R] [tz=OFFSET] [allday=yes] [prio=N]
[cat=LIST]` adds an event. `ID` is a name (letters, digits, `.`, `_`, `-`; up
to 32 characters, starting with a letter) or `-` for an automatic one.
Every event gets a sequence number, counted up from 1 (`idseq N` moves the
counter forward, to at most 2^50-1). Its reference is the shortest base-32
spelling of the number using `0-9A-Z` without I, L, O and U; `#REF` names an
event anywhere an id is expected. When reading a reference, I and L stand for
1, O for 0, and case is ignored. An automatic id is `E` and the reference.

Titles are normalised on input: blanks (spaces and tabs) at the ends are
removed and every run of blanks becomes one space. A title has 1 to 80
characters. Categories are written `a,b,c` (up to 8, each up to 24
characters, duplicates dropped); a comma or backslash inside a category is
written with a backslash in front of it.

Other event commands: `event show`, `event rm`, `event move REF START`,
`event rule REF RULE|none`, `event retitle`, `event cat REF LIST|-`,
`event set REF [dur=] [tz=] [prio=]`, `skip REF DATE`, `unskip REF DATE`,
`expand REF FROM TO` (local dates, at most 3660 days), `list`, `stats`.

## Rules

`FREQ[;key=value]...` with FREQ one of daily, weekly, monthly, yearly and keys
`every` (1 to 400), `on`, `monthday`, `count` (1 to 1000) and `until`
(inclusive). `on` lists weekdays (`MO,WE`) for weekly rules and positioned
weekdays (`2TU`, `-1FR`; positions 1 to 5 or -1 to -5) for monthly rules;
`monthday` (1 to 31) is for monthly rules without `on`. Keys may come in any
order and either case; the program writes the canonical form (fixed key
order, weekdays in week order, `every=1` left out).

A series begins at the first date on or after the start date that the rule
selects. Daily: every `every` days. Weekly: the selected weekdays (the start's
weekday by default) in every `every`-th week, counting weeks from the week of
the start. Monthly: every `every`-th month; a `monthday` or start day that the
month lacks becomes the month's last day; positioned weekdays that a month
lacks are left out. Yearly: the start's month and day; 29 February becomes 28
February in other years. `count` counts every date of the series including
skipped ones. A window more than 50000 dates into a series is refused.

`skip` removes one occurrence from listings; it must name an occurrence and
the event must recur. `event move` and `event rule` keep only the skips that
still name an occurrence of the changed series.

## Listings

* `agenda FROM TO [n=N]` lists occurrences whose UTC start is in the window
  (UTC dates, at most 400 days), ordered by UTC start, then priority (higher
  first), then id in natural order (digit runs compare by value, a shorter
  spelling of equal digits first). `busy FROM TO` merges the spans of those
  occurrences; spans that overlap or touch are merged.
* `shift DATE N UNIT` adds days, weeks, months or years; a month or year step
  keeps the day of the month when it can and otherwise lands on the last day.
* Helpers: `ordinal DATE`, `date N`, `weekday DATE`, `offset TEXT`,
  `dur TEXT`, `snap START`, `title TEXT`, `rule TEXT`, `ref N`, `unref TEXT`.

## Export and import

`export text` writes one record per event: `E|id|seq|title|start|raw|dur|rule|
tz|flags|prio|cats|skips`. Inside a field a backslash is `\\`, a vertical bar
`\p` and a tab `\t`. `export pack` writes `pack SUM HEX`: a frame of
length-prefixed packed records with a 16-bit Fletcher checksum `SUM`.
`import rec RECORD` and `import pack SUM HEX` add events (refused when an id or
number is already used or a record breaks the rules above).

## Properties and the self-check

After every command the program checks its own state; `check` checks
everything. The properties are:

1. A day converts to a calendar date and back to the same day.
2. An offset written as text reads back as the same minutes.
3. Escaping is lossless: a title or a category list read back from its
   escaped text is the original.
4. A stored title is already normalised: normalising it again changes nothing.
5. A start is on a minute boundary and within 30 seconds of what was given.
6. A packed record and a one-event frame decode to the event they came from,
   and so does its text record.
7. A rule's text is canonical. A weekly series stays inside the weeks the rule
   selects; a daily series keeps its step; a series is increasing and respects
   `count` and `until`.
8. Skips are increasing and each names an occurrence of the event's series.
9. A reference reads back as its number and has no leading zeros.
10. The agenda order above holds, including the id order for ties.

If a property fails the program prints `INVARIANT: ...` on standard error and
exits with status 86. Otherwise the exit status is 0.
