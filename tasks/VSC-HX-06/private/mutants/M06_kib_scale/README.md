# relaydesk

Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.

relaydesk is a toy simulator of a message relay: senders hand messages to
the relay, the relay cuts them into fragments and delivers them to
recipients over simulated links, with priorities, fairness between senders,
retries, duplicate detection, per-recipient limits and quiet hours, message
lifetimes (TTL), statistics, billing and an audit log. Everything is
invented, runs locally on a logical clock, and touches no files or network.

Run: `python3 main.py < commands.in` (Python 3.12, standard library only).
Build / syntax check: `sh build.sh`.

## Input

Input is UTF-8 text, one command per line (LF or CRLF line ends). Blank
lines and lines whose first non-blank character is `#` are ignored.
*Blanks* are spaces and TABs; a *token* is a run of non-blank characters.
A trailing `TEXT` argument is the rest of the line after the preceding
tokens, blanks trimmed at both ends; it may contain any character.

`batch` is followed by a data block: every following line up to a line that
consists of `.end` (blanks around it allowed) belongs to the block.

Names of senders and recipients match `[a-z][a-z0-9_-]{0,23}`; message ids
match `[A-Za-z0-9][A-Za-z0-9_.-]{0,31}`.

A refused command prints `ERROR <command>: <reason>` and changes nothing;
processing continues with the next line. (In a batch, a refused block line
prints `ERROR batch: line N: <reason>` and the other lines still count.)

## Time

The logical clock starts at `d0 00:00:00.000` (day 0, UTC) and only moves
with `advance` and `at`. Instants are printed `dN HH:MM:SS.mmm` in UTC.
Internally every instant and duration is an integer number of milliseconds.

* duration: digits followed by `ms`, `s`, `m`, `h` or `d` (`1500ms`, `90s`, `2h`);
* instant: `dN HH:MM`, `dN HH:MM:SS` or `dN HH:MM:SS.mmm`;
* UTC offset: `+HH:MM` / `-HH:MM`, at most 14:00 either way;
* time of day: `HH:MM` (local time of a recipient).

Every recipient has a fixed UTC offset (`tz=`, default `+00:00`, no
daylight saving). Its *local time* is UTC plus the offset; its *local day*
runs from local midnight to local midnight (for a recipient west of UTC the
first hours of d0 belong to local day -1).

## Configuration

Values have three layers; a later layer wins: built-in default, global
(`set KEY VALUE`), per recipient (`set-for RECIPIENT KEY VALUE`, only for
keys of scope *recipient*; `unset-for RECIPIENT KEY` removes it). Values are
non-negative integers in the unit shown, except the quiet-hours keys which
take `HH:MM` or `-` (not set). A value out of range is refused. A change
applies from the next thing that happens (the next acceptance, round or
report); it does not rewrite what already happened.

| Key | Unit | Scope | Default | Range | Meaning |
|---|---|---|---|---|---|
| dispatch.interval_ms | ms | global | 1000 | 100..60000 | time between dispatch rounds |
| dispatch.batch | count | global | 4 | 1..100 | attempts per round |
| dispatch.per_recipient | count | recipient | 1 | 1..100 | attempts per recipient per round |
| frag.size_bytes | bytes | global | 32 | 4..65536 | largest fragment |
| retry.base_ms | ms | global | 2000 | 1..600000 | wait after the first failed attempt |
| retry.factor | count | global | 2 | 1..10 | wait multiplier per further failure |
| retry.cap_s | s | global | 60 | 1..86400 | longest backoff wait |
| retry.max_attempts | count | recipient | 4 | 1..10 | attempts per fragment |
| dedup.window_s | s | recipient | 300 | 0..86400 | duplicate detection window |
| ttl.default_s | s | recipient | 3600 | 1..604800 | TTL when `send` gives none |
| ttl.max_s | s | recipient | 86400 | 1..604800 | longest TTL |
| queue.max_pending | count | recipient | 50 | 1..10000 | pending messages per recipient |
| limit.daily | count | recipient | 0 | 0..100000 | messages started per local day (0 = none) |
| limit.hourly | count | recipient | 0 | 0..100000 | messages started per rolling hour (0 = none) |
| limit.daily_kib | KiB | recipient | 0 | 0..1048576 | bytes started per local day, in KiB of 1024 bytes (0 = none) |
| quiet.start | HH:MM | recipient | - | | start of quiet hours (local) |
| quiet.end | HH:MM | recipient | - | | end of quiet hours (local) |
| breaker.threshold | count | recipient | 3 | 1..100 | failures in a row before a pause |
| breaker.pause_s | s | recipient | 30 | 1..86400 | length of a pause |

`config [RECIPIENT]` lists `KEY VALUE UNIT SOURCE` lines (source `default`,
`global` or `recipient`); with a recipient, only keys of scope recipient.

## Senders, recipients, links

* `sender NAME PLAN` — PLAN is `basic`, `bulk` or `pro` (see Billing).
* `recipient NAME [tz=OFFSET]`
* `link RECIPIENT fail N` / `lost N` / `busy N SECONDS` / `ok` — scripts the
  outcome of the next N attempts to RECIPIENT (appended to what is already
  scripted); `ok` clears the script. Unscripted attempts succeed. Outcomes:
  * `ok`: the recipient received the fragment and acknowledged it;
  * `fail`: the fragment did not arrive;
  * `busy`: the fragment did not arrive and the recipient asks the sender to
    wait at least SECONDS seconds before the next attempt of that fragment;
  * `lost`: the fragment arrived but its acknowledgement was lost, so the
    sender sees a failure (printed `lost-ack`).

## Sending

`send ID SENDER RECIPIENT [prio=P] [ttl=DURATION] [after=DURATION] TEXT`

`batch SENDER RECIPIENT [prio=P] [ttl=DURATION] [after=DURATION]`, followed
by a block of `ID TEXT` lines. Each block line is handled exactly like a
`send` with the batch's sender, recipient and options.

Options come right after RECIPIENT, in any order; the first token that is
not one of them starts TEXT. P is `urgent`, `high`, `normal` (default) or
`low`. Every message, from whichever command, goes through the same checks
in this order; the first one that applies decides:

1. the id must be unused (an id is used once its message has been
   accepted), the sender and recipient must exist, TEXT must be non-empty
   (otherwise ERROR);
2. **duplicates**: if the same sender sent the same TEXT to the same
   recipient and that earlier message was accepted less than the
   recipient's `dedup.window_s` ago, the message is a duplicate:
   `DUP ID of EARLIER`. Only accepted messages are remembered for this, and
   the window always counts from the remembered acceptance (a duplicate
   does not restart it; a later acceptance of the same text does);
3. **capacity**: if the recipient already has `queue.max_pending` pending
   messages: `REJECT ID queue-full`;
4. **acceptance**: `ACCEPT ID SENDER->RECIPIENT prio=P frags=N size=B ttl=T`
   (plus ` after=A` when given). The message's TTL is `ttl=` or the
   recipient's `ttl.default_s`, but never more than its `ttl.max_s`. Its
   *deadline* is acceptance + TTL. With `after=`, no fragment is attempted
   before acceptance + A (the TTL still counts from acceptance).

The body is cut into fragments of at most `frag.size_bytes` bytes of its
UTF-8 encoding, never inside a character. `size` is the body's length in
bytes.

A message is *pending* from acceptance until it reaches one of the final
states delivered, failed, expired or cancelled. `cancel ID` cancels a
pending message (`CANCEL ID`).

### Direct attempts

An urgent message that has a single fragment, no `after=`, and whose
recipient has no other pending message and is not paused, is attempted at
once at acceptance (printed with ` direct`), provided the recipient's limits
let it start (Limits); otherwise it waits for the dispatch rounds like any
other message. A direct attempt is an ordinary attempt in every respect
(retries, pauses, sender turns, statistics, billing).

## Dispatch

Dispatch rounds happen at every multiple of `dispatch.interval_ms` on the
clock. `advance D` moves the clock by D and `at INSTANT` to INSTANT
(not earlier than now); every round in (now, new now] runs in order. A
round at instant t:

1. ends the pauses whose end is <= t (`RESUME R`);
2. expires every pending message whose deadline is <= t (`EXPIRE ID`), in
   acceptance order;
3. makes up to `dispatch.batch` attempts, each time on the first eligible
   fragment in dispatch order, and settles each attempt before choosing
   the next one.

A fragment is *eligible* at t when it is not yet acknowledged, its message
is pending, its next-attempt time is <= t, its recipient is not paused and
has had fewer than `dispatch.per_recipient` attempts in this round, the
recipient is not in quiet hours (urgent messages ignore quiet hours), and,
if its message has not started yet, the recipient's limits let it start.

### Dispatch order

Among eligible fragments, compare in turn:

1. priority: urgent, high, normal, low;
2. sender turn: the sender whose most recent attempt is the oldest comes
   first; a sender with no attempt yet comes before every other sender.
   Attempts are totally ordered by when they are made: of two attempts in
   the same round, the later one is the more recent;
3. the acceptance order of the message: a fragment keeps the place of its
   message for its whole life, retries included;
4. the fragment number.

### Attempts and retries

Each attempt prints `SEND ID K/N SENDER->RECIPIENT OUTCOME` (outcome `ok`,
`fail`, `busy` or `lost-ack`). After a failed attempt (fail, busy or lost)
of a fragment that has now made n attempts:

* if n has reached the recipient's `retry.max_attempts`, the message fails:
  `FAIL ID K/N attempts=n`;
* otherwise the next attempt is due at `now + wait`, with
  `wait = min(retry.base_ms * retry.factor^(n-1), retry.cap_s)`; for busy,
  wait is at least the SECONDS the recipient asked for. If that instant is
  at or after the message's deadline, the message expires now
  (`EXPIRE ID`); otherwise `RETRY ID K/N at INSTANT`.

### Reassembly

The recipient keeps the fragments it received. A fragment can arrive more
than once (a lost acknowledgement leads to a retry); the copy that is
already there counts. The message is delivered at the moment the recipient
holds every fragment 1..N: `DONE ID SENDER->RECIPIENT size=B cost=C`; the
body is the fragments in order, and any attempt still due for the message
is dropped. `inbox R` lists delivered messages in delivery order.

### Pauses

Every failed attempt adds one to the recipient's count of failures in a
row; every acknowledged attempt resets that count to zero. When the count
reaches `breaker.threshold`, the recipient is paused for `breaker.pause_s`
(`PAUSE R until INSTANT`) and the count starts again from zero.

### Quiet hours

A recipient with both `quiet.start` and `quiet.end` set and different is
in quiet hours when its local time of day is in [start, end); the window
may run over midnight (start later than end).

## Limits

A message *starts* when its recipient first receives one of its
fragments (outcome ok or lost). Before a message may start, it is checked
against the messages that already started for the same recipient:

* `limit.daily`: fewer than this many started on the recipient's current
  local day;
* `limit.hourly`: fewer than this many started in the rolling hour, that is
  less than 60 minutes before now (one that started exactly 60 minutes ago
  no longer counts);
* `limit.daily_kib`: the bytes of the messages started on the current local
  day plus this message's size do not exceed the limit (1 KiB = 1024 bytes).

A message that may not start waits (it is not printed); limits never stop
a message that has started. These rules hold for every path that can start
a message.

## Billing

Each delivered message is billed to its sender as one line:
`(base + rate * size / 1024) * factor` cents, with

| Plan | base (cents) | rate (cents per KiB) |
|---|---|---|
| basic | 1.5 | 0.8 |
| bulk | 0.6 | 0.4 |
| pro | 2.5 | 0 |

and factor 1.5 for urgent, 1.2 for high, 1 otherwise. **Each line is
rounded to whole cents, half up; every total, subtotal and revenue figure
is the sum of the rounded lines.** Amounts print as `D.CC`.

* `invoice SENDER`: the lines not yet invoiced, in delivery order, as
  `ID INSTANT RECIPIENT size=B prio=P AMOUNT`, then `total=T lines=N`;
  they are then invoiced (invoice numbers count per sender from 1). With
  nothing to bill: `invoice SENDER: nothing to bill`.
* `plans`: per plan `plan NAME messages=N revenue=R`, then
  `all messages=N revenue=R`.
* `report senders`: senders by revenue (highest first, then by name).

## Reports and listings

* `stats`: counters, `revenue=`, and per recipient: delivered messages and
  bytes, messages and bytes started on its current local day (`today`,
  `today-bytes`), messages started in the rolling hour (`hour`), its
  failures in a row and its last delivery.  `stats R` shows the same
  figures for one recipient together with its limits, pending messages,
  pause and unused scripted outcomes.
* `queue`: fragments not yet acknowledged, in dispatch order (ignoring
  eligibility).
* `show ID`, `history ID`, `inbox R`, `now`, `report daily R` (deliveries
  per local day of R), `report retry`, `doctor` (configuration and state
  warnings).
* `explain ID`: for each unacknowledged fragment of a pending message,
  every reason it cannot be attempted at the current instant.
* `forecast R SIZE`: the earliest instant at which R's limits let a new
  message of SIZE bytes start (limits only; read-only).
* `latency [R]`: delivery time (acceptance to last acknowledgement) of
  delivered messages: nearest-rank percentiles, minimum, mean (floored to
  the millisecond) and a histogram.  `timeline ID`: the events of one
  message with the time since acceptance.
* `snapshot`: a deterministic dump of non-default configuration, parties
  and messages.  `help [COMMAND]`: command synopses.
* `audit [N]`: the audit log (operator actions and pauses), all or the
  last N entries.

## Exports

`export deliveries [RECIPIENT]`, `export billing [SENDER]`, `export audit`
print CSV: a header line, then one line per record. A field is quoted with
`"` when it contains `,`, `"`, CR or LF or starts or ends with a blank;
inside quotes `"` is doubled.

## Invariants

relaydesk checks its own consistency. If any of these fails, it prints
`INVARIANT: <reason>` on standard error and exits with status 86 (output
printed so far is kept):

* right after an acceptance, the recipient has at most `queue.max_pending`
  pending messages;
* a delivered message's reassembled body has exactly its declared size;
* after every command: the counters match the message states, every
  delivered message has exactly one billing line, the per-recipient
  delivery counts add up to the total, and every queued fragment belongs to
  a pending message and is not acknowledged.

At the normal end of input the exit status is 0.
