# ledgerkeep

ledgerkeep is a toy, single-process simulator of a small ledger service. It
keeps accounts in a fixed slot table, posts deposits, withdrawals, transfers,
captures of holds and reversals to an append-only journal, compacts that
journal, hands posted records to a simulated clearing house in settlement
batches, and remembers idempotency keys so that a retried request is not
applied twice. It is meant to run for a long time on one command stream.
Nothing here touches the network or the wall clock. Time is a logical clock
that only moves when a command says so.

Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5
xhigh, 2026-10-29.

## Running

    sh build.sh                 # byte-compiles every module (syntax check)
    python3 main.py < script    # runs a command script

Python 3.12, standard library only. Commands come from standard input, one
per line; results go to standard output. The program exits 0 at the end of
the input, or 86 when its consistency check fails (see "Consistency check").

## Input format

* Blank lines and lines starting with `#` are ignored and print nothing.
* A line is split into tokens at spaces and tabs. A token `name=value` whose
  name is a lower-case identifier is an option; every other token is a word.
  Giving an option twice is an error.
* A malformed or impossible command prints `error: MESSAGE` and changes
  nothing; the program carries on with the next line.
* A money operation refused by a rule prints `deny CODE [DETAIL]` and
  changes nothing (see "Debit rules").

## Units

* Time is an integer number of milliseconds on the logical clock, which
  starts at 0. A duration is written `NUMBER[ms|s|m|h|d]`; a bare number
  is milliseconds.
* A day is `[k*86400000, (k+1)*86400000)` for an integer k; a minute is
  `[k*60000, (k+1)*60000)`.
* Money is an integer number of cents. It is written `12`, `12.5` or
  `12.50` and printed with two decimals (`12.50`, `-3.00`). Amounts of
  operations must be positive. No balance may exceed 1000000000.00.

## Commands

    clock | clock set TIME | clock advance DURATION       -> now=MS

    open NAME [overdraft=AMOUNT] [daily=AMOUNT] [velocity=N] -> open NAME slot=S gen=G
    close NAME                                            -> close NAME slot=S
    accounts                                              -> NAME slot=S gen=G balance=X held=Y ops=N ...
    balance NAME      -> NAME balance=X held=Y available=Z spent_today=W debits_last_hour=N

    deposit NAME AMOUNT [key=K]                -> ok TXID deposit NAME AMOUNT balance=X
    withdraw NAME AMOUNT [key=K]               -> ok TXID withdraw NAME AMOUNT balance=X
    transfer FROM TO AMOUNT [key=K]            -> ok TXID transfer FROM->TO AMOUNT balance=X
    reverse TXID                               -> ok TXID reverse TXID AMOUNT

    hold NAME AMOUNT [ttl=DURATION]            -> hold HID NAME AMOUNT until=MS|never
    capture HID [amount=AMOUNT] [to=NAME]      -> ok TXID capture HID NAME AMOUNT [to=NAME]
    release HID                                -> release HID NAME AMOUNT
    holds NAME                                 -> HID NAME AMOUNT until=MS|never ...

    show TXID | history NAME [last=N] | journal
    settle | clearing | clearing fail N | batches [last=N]
    idem | check

`balance=` in the deposit/withdraw/transfer lines is the balance of the
named (for a transfer: the debited) account after the operation.

## Accounts and slots

* An account name is a lower-case letter followed by up to 15 lower-case
  letters, digits or `_`. Only one open account may have a given name.
* `overdraft` (default 0) lets the balance go down to minus that amount.
  `daily` (default 500.00) is the daily debit limit and `velocity` (default
  30, from 1 to 1000) the debit count limit (see "Debit rules").
* The service has 256 account slots. `open` hands out slot 0, 1, 2, ... in
  order while some slot has never been used. After that, a freed slot is
  handed out again; the slot freed longest ago goes first. When no slot is
  free, `open` prints `error: no free slot`.
* Each slot has a generation, 0 when first used, one higher each time the
  slot is handed out again. Slot and generation together identify one
  account for its whole life.
* A newly opened account always starts fresh: balance 0, nothing held,
  nothing spent today, no debits in the last hour, `ops=0` and no
  idempotency keys, even when it reuses the slot or the name of an earlier
  account.
* `close` needs a zero balance (`error: account NAME balance not zero`) and
  no live holds (`error: account NAME has holds`).
* `ops=` counts the journal records that touch the account.
* `accounts` lists the open accounts sorted by name, then
  `accounts open=N`.

## Debit rules

A debit is a withdrawal, or the debited side of a transfer. Deposits,
captures and reversals are not debits. The checks run in this order; the
first that fails refuses the operation:

1. `available = balance + overdraft - held`. A debit larger than
   `available` is refused with `deny funds available=X`.
2. The amounts of the account's debits in the current day, plus this one,
   must not exceed `daily`: `deny daily limit=X spent=Y` (Y is what was
   spent before this operation). The tally starts at zero every day.
3. A debit made in minute m counts for minutes m, m+1, ..., m+59 and no
   longer from minute m+60 on. When the account already has `velocity`
   debits counting in the current minute, the debit is refused with
   `deny velocity limit=N`. `debits_last_hour` shows that count.

A refused operation changes nothing and is not remembered for idempotency.

## Idempotency keys

* `deposit`, `withdraw` and `transfer` accept `key=K` (1 to 32 letters,
  digits, `_` or `-`). A key belongs to one account: the named account for
  deposit and withdraw, the debited account for transfer. The same key text
  used with another account is a different key.
* When an operation carries a key that its account has already used for an
  accepted operation, it prints `replay TXID` (the id of that first
  operation) and changes nothing; its other arguments are not compared.
* The service remembers at most 64 keys. Storing a key (with an accepted
  operation) and replaying it both count as a use. When a key must be
  stored and 64 are remembered, the least recently used key is forgotten
  first. A forgotten key is new again. `idem` prints
  `idem entries=N capacity=64 evicted=E`.

## Transactions and the journal

* Every accepted deposit, withdrawal, transfer, capture and reversal gets
  the next transaction id and appends one record to the journal. Ids are
  printed `T<epoch>.<seq>`: `T0.0`, `T0.1`, ..., `T0.4095`, then `T1.0`,
  and so on. Refusals, errors and replays get no id.
* Records are numbered from 0 and kept in segments of 128 records: records
  0-127 form the first segment, 128-255 the second, and so on. A segment is
  sealed as soon as it holds 128 records.
* Compaction runs whenever a segment is sealed and at least 4 segments are
  sealed. It folds sealed segments into running totals, oldest first, and
  stops at the first sealed segment that still has a record not assigned to
  a settlement batch. Folded records are gone: `show` prints
  `TXID compacted`, `history` no longer lists them, and they cannot be
  reversed (`error: TXID is compacted`).
* `show TXID` prints the record: `TXID KIND FROM->TO AMOUNT at=MS` with
  `hold=HID` for captures, `reverses=TXID` for reversals and
  `reversed_by=TXID` once reversed. FROM or TO is empty for the outside
  world (`->alice` is a deposit). An id not issued yet is an error.
* `history NAME [last=N]` prints the account's live records, newest first,
  at most N (default 10, 1 to 1000), or `history NAME empty`.
* `journal` prints `journal records=N folded=F live=L segments=S sealed=X
  compactions=C` (S counts the live segments including the one being
  filled; C counts compactions that folded something).

## Reversal

`reverse TXID` posts a record that moves the original amount back. It is
refused (error) when the id was not issued, the record is compacted, it is
itself a reversal, it was already reversed (`error: TXID already reversed
by TXID`) or an account it touches is closed (`error: account NAME is
closed`; an account closed and reopened under the same name is a different
account). Reversals skip the debit rules and may take a balance below the
overdraft.

## Holds

* `hold NAME AMOUNT [ttl=DURATION]` reserves money: the amount must not
  exceed `available` (`deny funds available=X`); holds are not debits.
  `ttl` is from 1s to 1d; without it the hold never expires.
* Hold ids are `H001` to `H999`. A new hold gets the id after the one
  handed out last, going from `H999` back to `H001` and skipping ids of
  live holds. At most 500 holds may be live (`error: too many holds`).
* A hold with `until=T` expires when the clock reaches T. Expiry happens
  when the clock moves: after the `now=` line, one `expire HID NAME AMOUNT`
  line per expired hold, in order of deadline, then hold id.
* `capture HID [amount=A] [to=NAME]` ends the hold and takes A (default:
  all of it, at most all of it) from the account, to NAME or out of the
  service; the rest of the hold is freed. `release HID` ends the hold and
  frees all of it. An id that is not live is `error: unknown hold HID`.
* `holds NAME` lists the account's live holds by id, then
  `holds NAME count=N held=X`.

## Settlement

* `settle` puts the next records not yet assigned to a batch (at most 100,
  in journal order) into a new batch `B<n>` and submits it at once; with
  nothing unassigned it prints `settle nothing`. Line:
  `batch B<n> n=N volume=X first=TXID last=TXID entry=E` (volume = sum of
  amounts), then the result of the submission.
* An outstanding batch occupies one of 16 table entries. Entries are used
  round robin: the search starts after the entry handed out last and takes
  the first free one. With all 16 busy, `settle` prints
  `error: settlement backlog full`.
* Every batch has its own attempt count, starting at 0. A submission is
  one attempt. On success: `batch B<n> settled`. After failed attempt k
  with k < 4: `batch B<n> failed attempt=k retry_at=MS`, the retry being
  due 30s * 2^(k-1) after the failure. After the 4th failed attempt:
  `batch B<n> parked attempts=4`. Settled and parked batches free their
  entry.
* Due retries are submitted when the clock moves (after expiries), in
  order of due time, then batch number.
* `clearing fail N` makes the next N submissions fail; `clearing` prints
  `clearing fail_next=N submitted=S accepted=A`.
* `batches [last=N]` prints the last N batches (default 10):
  `B<n> pending n=N volume=X attempt=K retry_at=MS entry=E` or
  `B<n> settled|parked n=N volume=X attempts=K entry=E`, then
  `batches total=T pending=P unassigned=U`.

## Consistency check

After every command the program checks its counters (journal record and
index counts, folded versus assigned records, batch accounting, limits on
keys, holds and slots). `check` and the end of the input run the full
check as well: every open account's balance equals what the journal
(folded totals plus live records) says, the held amount equals the sum of
its live holds, nobody has spent more today than their daily limit, and the
journal index points at the right records. `check` then prints
`check ok records=N live=L accounts=A holds=H batches=B`. When a check
fails, the program prints what it had so far, then `INVARIANT: MESSAGE` on
standard error, and exits with status 86.
