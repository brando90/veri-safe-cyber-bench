# chillroute

A toy cold-chain shipment monitor. Temperature loggers travel with
shipments along routes of stops; `chillroute` stores their readings, finds
runs of out-of-band readings, raises alerts, scores each shipment against its
temperature band, ranks shipments, keeps a custody chain and writes shipments
out as tab-separated text and reads them back.

Python 3.12, standard library only. Build with `sh build.sh` (it only
byte-compiles). Run with `python3 main.py < commands.txt`. Input must be
UTF-8; output is UTF-8.

## Input

One command per line. Blank lines and lines starting with `#` are ignored.
A line is split into words at blanks and tabs; a double quote starts a quoted
word that runs to the next unescaped double quote and may contain blanks and
the escapes `\"`, `\\`, `\n`, `\t`. A word `name=value` with a lower-case
`name` (not quoted) is an option. Output goes to standard output. A refused
command prints `error: MESSAGE` and the run goes on. `import` and `load` take
the lines that follow them up to a terminator line (`end export`, `end load`).

## Concepts

* A **site** has a code (2 to 6 letters or digits, starting with a letter,
  stored in upper case) and a name. A **route** is a list of 2 to 12 site
  codes. A **shipment** has an id (a letter, then up to 15 letters, digits,
  `_` or `-`), a label, a route and a temperature band.
* Temperatures are degrees Celsius with at most one decimal and are kept as
  integer tenths. A reading is **in band** when `min <= temp <= max`.
* A **reading** is an instant, a temperature and an optional humidity (whole
  percent). A shipment keeps its readings ordered by instant; a second
  reading at the same instant replaces the first.
* A **journey** opens at the arrival at stop 1 and closes at the arrival at
  the last stop of the route.
* An **excursion** is a run of consecutive out-of-band readings. It starts at
  its first out-of-band reading and ends at the first in-band reading after it.
  An excursion still running at the last reading ends there and is shown as
  `open`. Its kind is `high`, `low` or `mixed`; its peak is the reading
  farthest outside the band (the earliest one on a tie).
* Labels are cleaned when they are stored: Unicode normalisation form C, then
  every run of ASCII blanks (space, tab, CR, LF, FF, VT) becomes one space and
  the ends are trimmed. At most 40 characters. Only ASCII blanks collapse.

## Commands

Settings

* `set KEY VALUE` and `config`: settings `hold` (minutes, default 10),
  `keep` (minutes, default 0), `gap` (seconds, default 0), `cap` (default 600
  readings per shipment per clock hour), `slack` (minutes, default 15) and
  `spike` (tenths of a degree per minute, default 0).
* `site add CODE NAME`, `site list`, `site export`, `route add ID CODE...`,
  `profiles` (the cargo classes and their bands).
* `ship add ID LABEL route=R [class=C] [min=T] [max=T] [maxexc=M] [cap=N]
  [hmax=P] [skew=S] [offset=T]`, `ship edit ID options`, `ship show ID`,
  `ship list`, `ship rename ID LABEL`, `ship remove ID`. A class sets the band;
  `min`/`max` override it. `maxexc` (minutes) overrides `hold` for the
  shipment; `cap` overrides the global cap; `hmax` is a humidity ceiling in
  percent (no ceiling when absent); `maxexc=inherit`, `cap=inherit` and
  `hmax=inherit` remove the override. `skew` and `offset` describe the logger
  (see the conventions). The band must have `min` below `max`.

Data in

* `read ID t=SECONDS temp=DEGREES [hum=PERCENT]` stores a reading and prints
  nothing. When the shipment's intake cap for that clock hour is already
  used it prints `refused ID t=SECONDS cap`. A reading that replaces another
  one at the same instant does not count against the cap.
* `load ID` then rows `t,temp[,hum]` up to `end load`: each row goes through
  the same path as `read`. A first row starting with `t` is a header. Prints
  `ok load ID accepted=A refused=R bad=B`.
* `arrive ID stop=N t=SECONDS`, `plan ID stop=N t=SECONDS` (planned arrival),
  `handoff ID PARTY t=SECONDS`, `shift ID seconds=N` (moves every reading of
  the shipment by N seconds), `prune now=SECONDS [dry=yes]`.
* `import`: reads a block written by `export` and replaces the shipment of
  that id with the stored values exactly as they are written (no calibration,
  clamping or intake cap is applied again).

Data out

* `window ID [from=S] [to=S]`, `timeline ID [from=S] [to=S]` (instants as
  `dDAY HH:MM:SS`, the first day is `d1`), `describe ID [from=S] [to=S]`.
* `rollup ID`: one line per clock hour that holds readings, with count, minimum,
  maximum, mean and mean humidity.
* `excursions ID`, `alerts [ID] [kind=K]`, `sla ID`, `rank [by=sla|exposure|alerts]`,
  `find TEXT`, `legs ID`, `report ID`, `plans ID`, `custody ID`, `verify ID N sig=NN`,
  `forecast ID [minutes=N]`, `exposure ID`, `histogram ID [step=TENTHS]`,
  `compare ID ID`, `board`, `fleet`, `audit [N]`, `stats`, `help`,
  `export ID|all`, `site export`.

Alert kinds, in the order used for ties: `excursion` (an excursion lasting at
least the shipment's hold), `gap` (two consecutive readings more than `gap`
seconds apart; reported at the later reading), `late` (an arrival more than
`slack` minutes after its planned time), `spike` (a change between consecutive
readings of more than `spike` tenths per minute), `humid` (a run of readings
above `hmax`). Alerts are listed by instant, then kind, then shipment id.

`sla` is the share of in-band readings among the readings of the journey (all
readings while the journey is not closed). `rank` lists shipments with the
lowest share first and shipments without readings last. Averages, medians and
shares are rounded half up (towards positive infinity on exact halves).
Delays are truncated towards zero. `forecast` projects a straight line through
the last six readings.

## Conventions between modules

Where two modules meet, the module named in the last column owns the
convention. It is the contract: the other module adapts to it, and the
tests follow it.

| Boundary | Quantity | Convention | Owner |
|---|---|---|---|
| command text to every handler | instants and offsets in a command | decimal seconds, at most three decimals | command text |
| command text to `window`, `timeline`, `describe` | user ranges `from=` / `to=` | both ends included | command text |
| ingest, handlers to readings | stored instants | integer milliseconds since the start of the run | readings |
| readings to windows, rollup, excursions, alerts, retention, quota | instants | integer milliseconds; clock hour = `ms // 3_600_000` | readings |
| windows to every caller | time ranges | half-open `[start, end)` in milliseconds | windows |
| retention to readings | prune cutoff | readings before `now - keep` go; a reading exactly at the cutoff stays | retention |
| config to every consumer | durations | whole minutes (`hold`, `keep`, `slack`, `maxexc`); `gap` is whole seconds | config |
| config, shipments to quota | intake cap | readings per clock hour; `0` means unlimited; a shipment value (even `0`) overrides the global one | config |
| config, shipments to alerts | limits | `keep`, `cap`, `gap`, `spike`: `0` means off; `slack` and `hmax`: `0` is a real value | config |
| excursions to alerts, report, listings | excursion length | whole seconds, rounded down; start and end stay milliseconds | excursions |
| shipments to legs, report, handlers | stop numbers | 1-based, as typed; places keeps stops in 0-based lists | shipments |
| shipments (skew) to ingest | logger clock skew | whole seconds, positive means the logger clock runs ahead of the reference | shipments |
| ingest to calib | clock correction | `calib.correct(ts, offset)` adds the offset to the instant | calib |
| ingest, units to calib | temperatures | integer tenths; stored values lie in -40.0 to 60.0; calibration is applied first and the clamp last | calib |
| export to tsvfmt | text records | `row` joins fields as given; the writer escapes free text (`esc`, or `erow`); `split_row` unescapes | tsvfmt |
| sla to ranking, board, fleet | scores | integer tenths of a percent, half up; equal scores are ordered by shipment id, natural order | sla |
| textnorm to shipments, search | labels and queries | labels are stored cleaned; a query is compared after the same cleaning and `casefold` | textnorm |
| lexer to handlers | quoted words | the word without quotes, escapes resolved | lexer |
| handoffs | signature | two digits from the UTF-8 bytes of the party and the whole seconds of the instant | handoffs |
| rollup, forecast, exposure | rounding | half up on exact halves, integer arithmetic only | units |

## Export format

`export ID` prints `begin export`, one `ship` line (id, label, route, min, max,
maxexc, cap, hmax, skew, offset; `-` for an absent value), one `r` line per
reading (instant in milliseconds, tenths, humidity or `-`), one `arr` line per
arrival (stop, instant in milliseconds), one `plan` line per planned arrival,
and `end export`. Fields are separated by one tab. `site export` prints the
sites between `begin export sites` and `end export sites`. Reading an export
back and writing it again gives the same text.

## Errors

A refused command prints one line `error: MESSAGE`; nothing in the run changes.
Examples: `no such shipment X`, `no such site X`, `no such route X`,
`duplicate shipment X`, `bad temperature T`, `bad time T`, `X out of range`,
`band needs min below max`, `label too long`, `empty label`, `stop out of range`,
`arrival out of order`, `unknown command X`, `unterminated quote`, `bad escape`,
`block is not closed`, `bad import block`, `empty range`, `empty query`,
`need at least two readings`, `corrected time is before the start of the run`.
The audit log keeps the last 200 command lines and numbers them from 1.
