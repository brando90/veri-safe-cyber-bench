# billmill

`billmill` is a toy usage-metering and invoicing engine. It keeps customers on
plans, records metered usage of cloud-style services, turns each closed
billing period into an invoice (plan fee, usage charges, coupons, tax), and
tracks payments, credit, refunds and late fees. It has no files and no
network: it reads commands from standard input, one per line, and prints the
results on standard output. Run it as `python3 main.py < commands.txt`.

The code is split into small modules. Service rating, tax regions, coupon
kinds, currencies, customer setters and reports each have one module per
item; the shared helpers (`money`, `timeutil`, `invoice`, `ledger`) are used
by all of them.

## Input and output

* A line is words and `name=value` options separated by blanks. A double
  quote starts a quoted part that may contain blanks. Blank lines and lines
  starting with `#` are skipped.
* A command that fails prints one line `error: MESSAGE` and changes nothing.
  Commands that succeed print what they did.
* After every command the program checks its own books (see the last
  section). A failed check prints `INVARIANT: ...` on standard error and the
  run ends with exit status 86. Otherwise the exit status is 0.
* Money is printed in major units with the currency's decimals (JPY 0, USD
  and most others 2, KWD 3). Amounts typed in commands use the same form.
  Inside the program every amount is a whole number of minor units.

## Time and periods

The clock counts days from 0 and only moves with `tick DAYS`. A billing
period is 30 days: period 0 is days 0-29, period 1 is days 30-59, and so on.
`today` prints the day and the period.

## Customers

`customer add ID PLAN REGION CURRENCY [name=TEXT]` starts a customer on
today's day. Ids are 2-20 characters of lower-case letters, digits and
hyphens, starting with a letter. A customer has a plan, a tax region, a
currency, a payment term in days (default 30), an exempt flag and a few
free-text fields (`po`, `email`, `phone`, `note`) that the `set` commands
change: `set region|currency|terms|po|exempt|name|email|phone|note ID VALUE`.
A currency can only be changed while the customer has no invoices and no
credit. `customer close ID` retires a customer whose invoices are all
settled; any credit left is forfeited. `customer list [plan=] [region=]
[status=]` lists customers, `customer show ID` and `customer history ID` show
one, and `help [COMMAND]` prints the usage lines.

A closed customer cannot be changed: the commands that record usage, change
the plan, add or remove coupons, add credit, take a payment or use `set` are
refused with `customer ID is closed`. Closed customers are not invoiced.
Listings, statements, reports and the ledger still show them.

## Plans and plan changes

`plan list` and `plan show PLAN` show the plan fees (in US cents, the base
unit of all prices) and the free allowance of each service. The plan fee is
charged once per period, in arrears, on the invoice of that period.

A customer who starts in the middle of a period pays, on the first invoice,
the part of the fee for the days from the start day to the last day of the
period, both included (a customer who starts on day 12 pays for 18 days).
Part-period amounts are the fee times days over 30, rounded half up.

`plan set ID PLAN` moves a customer to another plan at once. The change is
billed on the invoice of the period it happens in, as one adjustment line:
the new plan's fee minus the old plan's fee, both for the days left in the
period. Days left run from the day of the change to the last day of the
period, both included. The period's own fee line is the fee of the plan the
customer was on before the period or, in the first period, at the start.

## Services and rating

`service list` and `service show SERVICE` describe each service: a block
size, a unit name, a mode, a minimum charge and a price list. For one
customer and one period the program adds up the units recorded in the period
for every service and rates each service separately:

1. The free allowance of the customer's plan on the last day of the period
   is subtracted. Nothing is billed if no units are left.
2. The remaining units are turned into blocks. A partial block is billed as
   a whole block, except for services whose mode is `whole`, which bill
   complete blocks only.
3. Blocks are priced by tier. Tier limits are inclusive: a tier with
   `upto=100` covers blocks 1 to 100 and the next tier starts at block 101.
   A tier without a limit covers all the remaining blocks.
4. If the service has a minimum charge it bills at least that much whenever
   it bills anything.

The result, in US cents, is converted for each line into the customer's
currency (`currency list` shows the rates; JPY has no decimals). A line is
only printed if it is not zero. `quote ID SERVICE UNITS` shows the rating of
a hypothetical amount and `advise ID SERVICE UNITS` compares the plans.

## Usage records

* `usage ID SERVICE UNITS [day=DAY] [id=TEXT]` records 1 to 1000000 units on
  `day` (default today). The day cannot be in the future or before the
  customer's start day, and the period the day falls in must not already be
  invoiced for that customer (a voided invoice no longer counts).
* A record may carry an id; resending a record whose id was already accepted
  is refused with `duplicate usage id ID`.
* `usage batch ID SERVICE Q1 Q2 ... [day=DAY] [id=PREFIX]` records several
  quantities in one command. With a prefix the records get the ids
  `PREFIX-1`, `PREFIX-2` and so on, and the whole batch is refused if any of
  them is a duplicate. The day rules are the same as for a single record.
* `usage list ID [SERVICE]` and `usage summary ID [PERIOD]` list records.

## Coupons

`coupon add ID KIND VALUE [until=DAY] [n=COUNT]` gives a customer a coupon;
`coupon rm ID NUMBER` removes it and `coupon list ID` lists them.
`coupon kinds` shows the kinds. A percentage kind takes a whole percent
between 1 and 100; a fixed kind takes an amount in the customer's currency.
Each kind names what it applies to: all lines, the plan fee lines or the
usage lines. `first_periods` gives its percentage on the first `n` invoices
that get something from it (default 3); `volume` gives a rebate on usage that
grows with the usage charge, capped by the coupon percentage.

When an invoice is built the coupons are applied in the order they were
added. A coupon is skipped if its period starts after `until`. The discount of
all coupons together never exceeds the invoice subtotal. Each time a coupon
takes something off an invoice its use is counted; voiding the invoice does
not give the use back.

## Invoicing

`invoice run [PERIOD]` invoices one closed period for every active customer
that started in or before that period and has no live invoice for it; the
default is the latest closed period. An invoice has, in this order, the plan
fee line, adjustment lines, usage lines (by service name), then the subtotal,
the discounts, the tax and the total. The issue day is the day of the run
and the due day is the issue day plus the customer's terms. Invoice numbers
are `INV-0001`, `INV-0002`, ... for the whole run and are never reused.
Credit the customer holds is applied to a new invoice at once, up to its
total. `invoice show NUMBER`, `invoice list` and `statement ID` display them.

## Tax

Each customer has a tax region (`region list`, `region show REGION`). The tax
base of an invoice is the sum of the lines whose kind the region taxes
(`kinds=` in the listing) minus the invoice's discount; if it is not
positive there is no tax. A tax-exempt customer is never charged tax. Tax is
computed once per invoice and rounded to a whole minor unit. Late fees are
not taxed.

## Payments, credit, refunds, voiding

* `pay ID AMOUNT` applies the payment to the customer's open invoices, the
  one that falls due first before the others (ties by invoice number); what
  is left becomes credit. `pay ID AMOUNT inv=NUMBER` pays one invoice of that
  customer; paying more than it still owes is refused.
* `credit add ID AMOUNT` adds credit by hand.
* `refund NUMBER AMOUNT` hands money back to the payer. The refunded amount
  becomes owed on the invoice again. A refund is recorded in the ledger and
  can be made for a closed customer.
* `void NUMBER` cancels an invoice. An invoice that still has net payments
  against it cannot be voided. The usage of its period can be invoiced again.

## Late fees

`dun` adds one late fee to every invoice that is overdue, has money
outstanding and has no late fee yet. An invoice is overdue from the day after
its due day. The fee is 1.5 percent of the outstanding amount, rounded half
up, but at least the currency's minimum (`currency list`). It is added to the
invoice as a `late` line and to its total.

## Reports, ledger, audit, export

* `report list` names the reports. `report NAME [cur=CODE] [cust=ID]` prints
  one; grouped reports end with one `total` line per currency. `report top
  CODE [N]` ranks customers by net revenue (subtotal minus discount plus late
  fees) in one currency, best first, ties by customer id.
* The aging report puts outstanding amounts in the buckets `current` (not
  overdue), `1-30`, `31-60`, `61-90` and `91+` days overdue.
* `ledger [ID] [kind=KIND]` lists every movement of money; `audit [COUNT]`
  lists the last entries of the audit log.
* `export invoices|ledger|audit|customers|usage csv|tsv` prints a header row
  and one row per record. CSV quotes fields that contain a comma, a double
  quote or a line break.

## The consistency check

After every command the program checks that every invoice's lines, discount,
tax, late fee and total agree; that no amount is negative except adjustment
lines; that exempt customers carry no tax; that refunds, payments and late
fees are consistent with each other and with the due day; that credit
balances agree with the ledger; and that invoice numbers and usage records are
in order.
