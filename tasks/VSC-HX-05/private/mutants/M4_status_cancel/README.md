# slotbook

Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.

slotbook is a toy back office for a small one-chair appointment business
(think of a barber or a dog groomer). It keeps users and roles, customers, a
service catalogue, appointments, invoices, payments and an audit log in an
in-memory sqlite database, and is driven by command lines on standard input.
Results go to standard output. Everything in it is invented and runs locally;
it has no network access and touches no files.

Run: `python3 main.py < commands.in` (Python 3.12, standard library only).
Build / syntax check: `sh build.sh`.

## Input

Input is UTF-8 text, one command per line (LF or CRLF line ends). Blank lines
and lines whose first non-blank character is `#` are ignored. *Blanks* are
spaces and TABs; a *token* is a run of non-blank characters. Command words
are case sensitive.

A trailing `NAME`, `TEXT` or `REASON` argument is the rest of the line after
the preceding tokens, with blanks trimmed at both ends. It may contain any
characters (quotes, backslashes, commas, `|`, `%`, inner TABs for notes and
reasons, ...).

`import` is followed by a data block: every following line up to a line
that consists of `.end` (blanks around it allowed) belongs to the block and
is not read as a command.

## Data is data

Values that come from input (names, notes, reasons, codes, import column
names and fields) are data:

* they are stored exactly as given and printed back exactly as stored;
* they never become part of SQL text, whether as values or as table or
  column names;
* they can never act as a separator or quote in machine-readable output:
  every CSV, TSV and audit-detail field is written with that format's
  escaping rule (see "Output formats"), whichever command writes it.

## Users, roles and permissions

The *actor* is the user on whose behalf commands run. At start the actor is
`nobody`, which holds no permission. `as USER` switches the actor. The
database starts with one user, `owner`, whose role is `owner`.

Every user has exactly one role. A role may have parent roles; a role's
*ancestors* are its parents, their parents, and so on. Every role carries
grant and deny rules for permissions. **A role holds a permission if and
only if the role itself or one of its ancestors grants it, and neither the
role nor any of its ancestors denies it.** A deny anywhere in the chain
wins over any grant; anything not granted is denied.

Built-in roles (they cannot be changed):

| Role | Parents | Grants | Denies |
|---|---|---|---|
| `viewer` | – | customer.view appt.view invoice.view report.view | – |
| `frontdesk` | viewer | customer.write appt.write | – |
| `trainee` | frontdesk | – | customer.write |
| `billing` | viewer | invoice.write payment.record export.run import.run | – |
| `manager` | frontdesk, billing | appt.cancel invoice.void service.write audit.view | – |
| `owner` | manager | user.manage role.manage | – |

Custom roles are created with `role-add` and changed with `role-grant` and
`role-deny`. A change to a role takes effect immediately, for that role and
for every role that inherits from it.

### Operations

Permissions belong to *operations*, not to command words:

| Operation | Permission |
|---|---|
| create or change a customer (add, note, archive) | customer.write |
| book an appointment, or change its status to done or noshow | appt.write |
| cancel an appointment (status becomes cancelled) | appt.cancel |
| add a service | service.write |
| create an invoice | invoice.write |
| record a payment | payment.record |
| void an invoice | invoice.void |
| add a user | user.manage |
| create or change a role | role.manage |
| read customers | customer.view |
| read services and appointments | appt.view |
| read invoices | invoice.view |
| read reports | report.view |
| read the audit log | audit.view |
| run an import | import.run |
| run an export | export.run |

**Rule:** a command needs the permissions listed for it in the command table
*and* the permission of every operation it performs, whichever command
performs it. The listed permissions are checked first, in the listed order,
before anything else. Permissions of operations that depend on the arguments
are checked after the command-line arguments have been validated and before
anything is changed. A missing permission is always reported as exactly
`ERROR denied: PERM` (the first missing one), and the command changes
nothing.

## Commands

IDs are written `C`, `A`, `I`, `P` (customer, appointment, invoice, payment)
followed by 1 to 6 digits; output always uses four or more digits (`C0007`).
`C7` and `C0007` name the same customer.

| Command | Listed permissions | Effect and output |
|---|---|---|
| `as USER` | – | switch actor (`nobody` allowed): `OK actor USER` |
| `whoami` | – | `actor USER role ROLE` (`role none` for nobody) |
| `perms ROLE` | – | the permissions ROLE holds, sorted: `ROLE: p1 p2 ...` or `ROLE: (none)` |
| `user-add USER ROLE` | user.manage | `OK user USER role ROLE` |
| `role-add ROLE PARENT[,PARENT...]` | role.manage | new custom role with the given parents (no rules): `OK role ROLE` |
| `role-grant ROLE PERM` | role.manage | add a grant rule to a custom role: `OK role ROLE grant PERM` |
| `role-deny ROLE PERM` | role.manage | add a deny rule to a custom role: `OK role ROLE deny PERM` |
| `customer-add PHONE EMAIL NAME` | customer.write | EMAIL may be `-`: `OK customer C0001` |
| `customer-note CUST [TEXT]` | customer.write | replace the note (empty TEXT clears it): `OK customer C0001 note` |
| `customer-show CUST` | customer.view | `customer C0001`, `name: ...`, `phone: ...`, `email: ...`, `note: ...`, `status: active\|archived` |
| `customer-find TEXT` | customer.view | names containing TEXT (literal, ASCII case-insensitive), by id: `C0001 NAME` (+ ` [archived]`), then `matches: N` |
| `customer-archive CUST` | customer.write | archive the customer and cancel all of the customer's booked appointments (oldest first): `OK archived C0001 cancelled N` |
| `service-add CODE MINUTES PRICE TAX NAME` | service.write | `OK service CODE` |
| `services` | appt.view | `CODE 30min 25.00 tax 8.25% NAME` by code, then `services: N` |
| `book CUST CODE DAY TIME` | appt.write | `OK appointment A0001` |
| `appt-status APPT STATUS` | appt.write | STATUS is done, noshow or cancelled; only a booked appointment can change: `OK A0001 booked -> STATUS` |
| `cancel APPT` | appt.cancel | same as `appt-status APPT cancelled` |
| `appts DAY` | appt.view | `A0001 09:00-09:30 C0001 CODE STATUS` by start time, then `appointments: N` |
| `invoice-create CUST [DISCOUNT]` | invoice.write | invoice all done, not yet invoiced appointments of CUST (by day and time): `OK invoice I0001 total 24.36` |
| `invoice-show INV` | invoice.view | header, one `line ...` per appointment, totals line |
| `pay INV AMOUNT METHOD` | payment.record | METHOD is cash, card or transfer: `OK payment P0001 balance 0.00` |
| `invoice-void INV REASON` | invoice.void | only an open invoice without payments: `OK void I0001` |
| `report revenue FROM TO [tsv]` | report.view | see "Reports" |
| `report tax FROM TO [tsv]` | report.view | see "Reports" |
| `report balances [tsv]` | report.view | see "Reports" |
| `export KIND FORMAT` | export.run | KIND is customers, services, appointments or invoices (reading KIND needs its read permission); FORMAT is csv or tsv |
| `import KIND` + block | import.run | KIND is customers, services, appointments or payments; see "Import" |
| `audit [N]` | audit.view | the last N (default all) audit rows, oldest first: `#SEQ ACTOR ACTION OBJECT DETAIL`, then `entries: N` |
| `audit-export` | audit.view, export.run | the whole audit log as TSV (columns seq, actor, action, object, detail) |

Value rules: USER and ROLE names are 1-16 characters `[a-z0-9_.-]` starting
with a letter (`nobody` is reserved). PHONE is 3-20 characters from
`0-9+()-`. EMAIL is `-` or `local@domain` without blanks. CODE is an upper
case letter followed by 1-7 upper case letters or digits. MINUTES is 5-480
in steps of 5. PRICE and AMOUNT are decimal amounts with at most two
decimals (`12`, `12.5`, `12.50`; AMOUNT must not be zero). TAX is a percent
with at most two decimals, at most 100. DISCOUNT is a whole percent 0-100.
DAY is a real date `YYYY-MM-DD`; TIME is `HH:MM` on a 5-minute grid. Names
are at most 80 characters, notes and reasons at most 200; a name may not
contain TAB, CR or LF, notes and reasons may contain TAB but not CR or LF.

The business has one chair, open 08:00 to 18:00: an appointment must start
and end within opening hours and must not overlap a booked or done
appointment on the same day. Archived customers cannot be booked or changed.

## Money

Amounts are integer cents and are printed with two decimals (`12.50`). A
percentage of an amount (discounts and taxes) is computed **per invoice
line** and rounded half up to the cent; every total, subtotal and report
figure is the sum of the rounded per-line amounts. For one line:
`discount = DISCOUNT% of price`, `net = price - discount`,
`tax = TAX% of net`, `total = net + tax`.

## Reports

Reports read invoice lines of invoices that are not void, whose appointment
day lies in FROM..TO (inclusive; FROM after TO is `ERROR bad-range: FROM TO`).

* `report revenue`: one line per service code (sorted)
  `CODE lines=N net=X tax=Y total=Z`, then `all lines=N net=X tax=Y total=Z`.
  TSV columns: service, lines, net, tax, total (last row `all`).
* `report tax`: one line per tax rate (ascending)
  `rate 8.25% lines=N net=X tax=Y`, then `all lines=N net=X tax=Y`.
  TSV columns: rate, lines, net, tax (rate written `8.25`; last row `all`).
* `report balances`: one line per customer with a non-void invoice, by
  balance (highest first) then id: `C0001 invoiced=X paid=Y balance=Z NAME`,
  then `customers: N`. TSV columns: customer, name, invoiced, paid, balance.

## Output formats

* **CSV** (`export ... csv`): a header row, then one row per record ordered
  by id/code, LF line ends. A field containing a comma, a double quote, CR
  or LF is wrapped in double quotes with inner double quotes doubled; other
  fields are written as they are.
* **TSV** (`export ... tsv`, `report ... tsv`, `audit-export`): a header
  row, then one row per record, fields separated by one TAB, LF line ends.
  In every field, backslash is written `\\`, TAB `\t`, LF `\n`, CR `\r`.
* **Audit detail**: `key="value"` pairs separated by single spaces, in the
  documented order. In every value, backslash is written `\\`, double quote
  `\"`, TAB `\t`, LF `\n`, CR `\r`.

Export columns: customers `id name phone email note status`; services
`code name minutes price tax`; appointments
`id customer service day time minutes status invoice` (`-` if not on a
non-void invoice); invoices `id customer status discount net tax total paid`.

## Import

```
import KIND
<header: column names separated by TABs>
<one TSV row per record>
.end
```

Columns per KIND (required unless marked optional):
customers `name phone email(optional, default -) note(optional, default empty)`;
services `code name minutes price tax`; appointments
`customer service day time`; payments `invoice amount method`.

* The header names columns from that list, in any order. A header that
  names a column twice, names any other column, or lacks a required column
  refuses the import: `ERROR import: duplicate column C`,
  `ERROR import: unknown column C`, `ERROR import: missing column C`.
* Rows use the TSV escapes above and must have one field per header column.
  Empty lines are skipped. Lines are numbered from 1 within the block (the
  header is usually line 1).
* Each row creates one record exactly as the corresponding command would
  (`customer-add`, `service-add`, `book`, `pay`), with the same validation
  and the same audit row.
* The block is all-or-nothing. A bad row refuses the whole import with
  `ERROR import: line N: <reason>` where `<reason>` is the text the command
  would print after `ERROR ` (for example `ERROR import: line 3: bad-phone: x`),
  `ERROR import: line N: bad escape`, or
  `ERROR import: line N: expected M fields, got K`. An empty block is
  `ERROR import: missing header`; a block without `.end` is
  `ERROR import: missing .end`.
* Success: `OK imported N KIND`.

## Audit log

Every command that creates or changes records writes one audit row per record
created or changed, in that order, with the actor's name. Actions and their
detail fields (in this order):

| Action | Object | Detail fields |
|---|---|---|
| user.add | user | role |
| role.add | role | parents (comma separated) |
| role.grant / role.deny | role | perm |
| customer.add | C id | name phone email note |
| customer.note | C id | note |
| customer.archive | C id | cancelled (count) |
| service.add | code | name minutes price tax |
| appt.book | A id | customer service day time |
| appt.status | A id | from to |
| invoice.create | I id | customer lines total |
| payment.add | P id | invoice amount method |
| invoice.void | I id | reason |

`customer-archive` writes the `appt.status` rows of the cancelled
appointments first, then the `customer.archive` row.

## Errors

A command that cannot be carried out prints one line starting with `ERROR `
on standard output, changes nothing (no audit row either), and processing
continues with the next line. Messages:

`usage: <command synopsis>`, `unknown-command: WORD`, `denied: PERM`,
`bad-name: X`, `bad-id: X`, `bad-phone: X`, `bad-email: X`, `bad-code: X`,
`bad-minutes: X`, `bad-money: X`, `bad-rate: X`, `bad-day: X`, `bad-time: X`,
`bad-percent: X`, `bad-method: X`, `bad-status: X`, `bad-count: X`,
`bad-range: FROM TO`, `empty: FIELD`, `too-long: FIELD`, `bad-text: FIELD`,
`unknown-user: X`, `unknown-role: X`, `unknown-perm: X`,
`unknown-customer: ID`, `unknown-service: CODE`, `unknown-appointment: ID`,
`unknown-invoice: ID`, `duplicate-user: X`, `duplicate-role: X`,
`duplicate-rule: ROLE grant|deny PERM`, `duplicate-service: CODE`,
`builtin-role: X`, `archived: ID`, `outside-hours: HH:MM`, `slot-taken: ID`,
`bad-transition: ID FROM -> TO`, `nothing-to-invoice: ID`,
`invoice-void: ID`, `invoice-paid: ID`, `overpayment: ID balance X`,
`import: ...` (see "Import").

An `ERROR db: ...` line means a database statement failed. Valid input never
produces it.

## Consistency check

After every command the program checks the database against what the
command is documented to have done: the schema is unchanged; every table's
row count changed exactly as expected; every table whose contents changed is
one the actor's permissions allow changing; every new audit row has a
well-formed detail with exactly the documented fields. If a check fails the
program prints `INVARIANT: <reason>` on standard error and exits with status
86 (output produced so far is kept). On valid input it never fails; a failure
indicates a bug in the program.

## Source layout

* `main.py` input loop and exit status
* `registry.py` command table and dispatcher
* `session.py` actor, permission checks, output buffering
* `roles.py` built-in roles and permission resolution
* `admin.py` `as`, `whoami`, `perms`, users and roles
* `customers.py`, `appointments.py`, `billing.py` command handlers
* `reports.py` reports
* `transfer.py` import and export
* `audit.py` audit log
* `formats.py` CSV, TSV and audit-detail formats
* `money.py` amounts and rounding
* `parse.py` tokens and value validation
* `store.py` all SQL
* `invariant.py` the consistency check
* `errors.py` exception types
