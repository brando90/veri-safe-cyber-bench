# stockyard

`stockyard` is a toy warehouse inventory and order-routing system. It keeps
stock in lots at twelve warehouses, takes customer orders, picks the
warehouses that fill them, reserves the stock, ships it with one of nine
carriers to one of nine delivery regions, and handles returns, transfers,
stock counts, expiry and backorders. It has no files and no network: it reads
commands from standard input, one per line, and prints the results on standard
output. Run it as `python3 main.py < commands.txt`.

The code is split into small modules. Warehouses, product categories,
carriers, regions, customer setters and reports each have one module per item;
the shared helpers (`money`, `timeutil`, `stock`, `orders`, `routing`) are used
by all of them.

## Input and output

* A line is words and `name=value` options separated by blanks. A double quote
  starts a quoted part that may contain blanks. Blank lines and lines starting
  with `#` are skipped.
* A command that fails prints one line `error: MESSAGE` and changes nothing.
  Commands that succeed print what they did.
* After every command the program checks its own books (see the last
  section). A failed check prints `INVARIANT: ...` on standard error and the
  run ends with exit status 86. Otherwise the exit status is 0.
* Money is kept in whole US cents and printed as dollars and cents (`12.34`).
  Weights are whole grams. Quantities are whole units.

## Time

The clock counts days from 0 and only moves with `tick DAYS`. Day 0 is a
Monday, so the weekday of a day is its number modulo 7 (0 = Monday ... 6 =
Sunday). `today` prints the day and the weekday. Hours of the day (0-23) only
appear as the `at=` option of `ship`.

## Customers

`customer add ID REGION [tier=TIER] [name=TEXT]` creates an account. Ids look
like `c-acme` (`c-` and 1-12 lower-case letters or digits). Tiers are `basic`
(the default), `silver` and `gold`; `tier list` shows what each earns. An
account also has a carrier preference (`auto` or a carrier code), a split flag
(default `yes`), a hold flag (default `no`), and the free-text fields `po`,
`email` and `note`. They are changed with
`set region|tier|carrier|split|hold|po|name|email|note ID VALUE`; for the
text fields the value `-` clears the field. `customer list [tier=] [region=]
[status=]` lists accounts, `customer show ID` and `customer history ID` show
one, `customer close ID` retires an account.

A closed account cannot be changed: `set` and `order add` are refused with
`customer ID is closed`. An account on hold cannot place orders.

## Stock

Stock is held in lots: one lot per receipt, with a quantity, a reserved
quantity (stock promised to orders) and an optional expiry day.

* `receive WAREHOUSE SKU UNITS [exp=DAY]` books a receipt as a new lot. The
  quantity is booked in whole packs of the category (rounded up to the next
  full pack unless the category is sold loose, see the special cases). A
  warehouse stores only the groups listed for it in the table below, and only
  hazard classes up to its maximum; it holds at most its capacity in units
  (all lots count, reserved or not).
* Shelf life. A category with shelf days gives each lot an expiry day: the day
  of receipt plus the shelf days. The expiry day is the last day the lot may
  be sold; from the next day the lot is expired. A lot is allocated to an
  order only while at least the category's margin days remain before its
  expiry (expiry day minus today is at least the margin).
* Pick order. Lots are used earliest expiry first, then by lot id; lots
  without an expiry come last, oldest lot id first.
* `adjust WAREHOUSE SKU DELTA` corrects the book count after a stock count. A
  positive delta is added to the newest lot of that sku in the warehouse; a
  negative delta takes units from the lots in pick order. Units that are
  reserved for orders cannot be counted away: the adjustment is refused if
  fewer free (unreserved) units are held.
* `transfer FROM TO SKU UNITS` moves free units that are not expired to
  another warehouse that stores the category. Lots keep their expiry day.
* `expire [WAREHOUSE]` writes off every lot whose expiry day is before today.
  Units of such a lot that were reserved go back to the backorder of their
  order line.
* `replenish [WAREHOUSE]` lists slots whose free sellable units are at or
  below the category's reorder point, with a suggested receipt of twice the
  reorder point less the units available, rounded to packs.
* `stock [WAREHOUSE] [sku=SKU]` lists lots and `ledger [WAREHOUSE] [kind=KIND]
  [sku=SKU]` lists every stock movement (`receive`, `ship`, `return`,
  `scrap`, `adjust`, `transfer_in`, `transfer_out`, `expire`).

## Orders and routing

`order add CUSTOMER SKU:QTY... [ref=TEXT]` places an order for an account.
The same sku given twice is added up. A category may limit the quantity on one
line (table below). A region refuses an order that contains goods of its ban
level (see the region table) or of a higher hazard class; `region show` prints
the exact rule. An order with a `ref` already used by the same customer is
refused as a duplicate.

Stock is reserved at once. A warehouse that can fill every line completely
from free sellable stock takes the whole order; if several can, the nearest to
the delivery region wins (distance is the number of zones between warehouse
and region, ties by warehouse code). If none can and the customer accepts
split shipments, each line is filled from the nearest warehouses in turn and
what cannot be filled stays on backorder. If the customer does not accept
split shipments the whole order waits on backorder.

An order is `open` (everything reserved), `partial`, `backorder` (nothing
reserved or shipped), `shipped` (nothing left pending, something shipped) or
`cancelled`. `order cancel NUMBER` releases what is reserved and drops what is
on backorder; units already shipped are not affected. `order show NUMBER` and
`order list [CUSTOMER] [state=STATE]` show orders.

`backorder run` offers freed stock to waiting orders, gold customers first,
then silver, then basic, oldest order first within a tier. Each order is
handled like a new order for its backordered lines.

## Shipping

`ship NUMBER [at=HOUR] [carrier=CARRIER]` ships everything reserved for an
order, one shipment per warehouse. Stock leaves the warehouse and the lots
shrink.

* Dispatch day. Goods ready at hour H (the `at=` option, default 10) on day D
  leave the same day if H is before the warehouse's cut-off hour, otherwise
  on the next day; then on the first day the warehouse is open.
* Carrier. The customer's carrier preference is used when it is a carrier;
  `auto` picks the cheapest carrier that serves the region, takes the weight
  and the hazard class (ties: shorter transit, then code). The `carrier=`
  option overrides the preference. A named carrier that cannot take the
  shipment is refused.
* Carrier charge. Each carrier has a rate (a fee per parcel plus a charge per
  started weight step), a zone surcharge per zone of distance, a fuel
  surcharge and a minimum charge. Surcharges are rounded half up to whole
  cents (the same helper as duty and padding). The weight of a shipment is the
  sum over its lines of the category weight of the quantity.
* Transit and delivery. Transit time grows with the distance. The parcel
  arrives that many days after dispatch, plus the region's customs days if the
  shipment carries duty, and moves on to the first day on which the region
  delivers.
* Freight. The freight charged is the carrier charge plus the region's remote
  fee. It is waived when the value of the whole order reaches the free-freight
  value of the customer's tier. Handling is the warehouse's pick fee plus its
  pack fee. Duty is charged on the goods value of a shipment when that value is
  above the region's duty-free amount.

`return NUMBER SKU QTY [cond=good|damaged]` takes back shipped units, up to
what was shipped and not yet returned, within the category's return days
counted from the day of the `ship` command (the day itself is day 0).
Returned goods in good condition are restocked as a new lot at the warehouse
that shipped the line last, unless the category never restocks; everything
else is scrapped.

## Reports

`report list` names them; `report NAME [wh=CODE] [cust=ID]` prints one (not
every report takes both options). `expiring` takes `days=N`: lots whose expiry
is between today and N days from today. `export orders|stock|shipments|ledger
csv|tsv` dumps a table.

## Reference tables

Warehouses (hours are 0-24; the cut-off rule above applies to each):

| code | zone | cut-off hour | dispatches on | capacity | max haz | stores groups | pick fee | pack fee |
|---|---|---|---|---|---|---|---|---|
| alder | 3 | 16 | Mon,Tue,Wed,Thu,Fri | 6000 | 1 | dry, bulk | 40 | 120 |
| birch | 5 | 15 | Mon,Tue,Wed,Thu,Fri | 4000 | 3 | dry, haz | 45 | 110 |
| cedar | 2 | 17 | Mon,Tue,Wed,Thu,Fri | 3000 | 1 | dry, bulk | 35 | 100 |
| dune | 6 | 14 | Mon,Tue,Wed,Thu,Fri | 2500 | 0 | cold, frozen | 60 | 150 |
| elm | 4 | 16 | Mon,Tue,Wed,Thu,Fri,Sat | 3500 | 1 | dry | 42 | 115 |
| fjord | 7 | 13 | Tue,Wed,Thu,Fri,Sat | 2800 | 0 | cold, frozen, dry | 55 | 130 |
| grove | 8 | 15 | Mon,Tue,Wed,Thu,Fri | 2000 | 3 | haz | 70 | 200 |
| harbor | 1 | 18 | Mon,Tue,Wed,Thu,Fri,Sat,Sun | 7000 | 1 | dry, bulk | 38 | 90 |
| iris | 4 | 24 | Mon,Tue,Wed,Thu,Fri | 3200 | 1 | dry | 44 | 105 |
| juniper | 5 | 14 | Mon,Tue,Wed,Thu,Fri | 3000 | 0 | dry, cold | 5 | 95 |
| kelp | 9 | 0 | Mon,Tue,Wed,Thu,Fri | 400 | 1 | dry | 50 | 125 |
| larch | 3 | 15 | Mon,Tue,Wed,Thu,Fri,Sat | 4500 | 1 | dry, bulk | 41 | 112 |

Categories:

| code | group | pack | unit g | shelf days | margin days | max per line | reorder at | haz | return days | returns restocked |
|---|---|---|---|---|---|---|---|---|---|---|
| fasteners | dry | 100 | 12 | - | 0 | 5000 | 400 | 0 | 30 | yes |
| cables | dry | 50 | 85 | - | 0 | 2000 | 100 | 0 | 30 | yes |
| paper | dry | 10 | 450 | - | 0 | 600 | 40 | 0 | 14 | yes |
| tools | dry | 6 | 900 | - | 0 | no limit | 12 | 0 | 30 | yes |
| electronics | dry | 4 | 350 | - | 0 | 200 | 20 | 1 | 14 | yes |
| glassware | dry | 12 | 600 | - | 0 | 300 | 24 | 0 | 7 | yes |
| apparel | dry | 20 | 300 | - | 0 | 1000 | 60 | 0 | 60 | yes |
| snacks | dry | 24 | 120 | 180 | 14 | 2000 | 96 | 0 | 7 | never |
| dairy | cold | 12 | 500 | 21 | 3 | 500 | 36 | 0 | no returns | never |
| produce | cold | 10 | 800 | 7 | 1 | 400 | 30 | 0 | 2 | never |
| medicine | cold | 20 | 150 | - | 30 | 100 | 40 | 0 | 14 | never |
| frozen | frozen | 8 | 450 | 120 | 10 | 300 | 24 | 0 | no returns | never |
| solvents | haz | 6 | 1100 | - | 0 | 120 | 12 | 3 | 14 | never |
| lumber | bulk | 10 | 2350 | - | 0 | 800 | 50 | 0 | 30 | yes |

Carriers (money in cents; weights in grams):

| code | base | step g | per step | parcel g | total limit g | minimum | zone bp | fuel bp | transit | haz max | serves |
|---|---|---|---|---|---|---|---|---|---|---|---|
| swift | 450 | 500 | 60 | 20000 | none | 600 | 300 | 800 | 1 + 1 per 3 zones | 1 | all |
| parcelo | 700 | 1000 | 0 | 25000 | none | 700 | 200 | 700 | 2 + 1 per 3 zones | 0 | all |
| haul | 900 | 1000 | 40 | none | none | 1500 | 150 | 600 | 3 + 1 per 2 zones | 3 | all |
| aero | 1200 | 500 | 90 | 15000 | none | 1500 | 400 | 900 | 1 + 1 per 3 zones | 1 | all |
| nord | 500 | 500 | 55 | 20000 | none | 650 | 250 | 850 | 2 + 1 per 3 zones | 3 | all |
| gull | 400 | 500 | 50 | 18000 | none | 500 | 350 | 750 | 2 + 1 per 2 zones | 1 | all |
| tern | 480 | 500 | 65 | 20000 | none | 600 | 300 | 800 | 2 + 1 per 4 zones | 3 | arden, brook, crest, delta, ember, forge |
| pony | 300 | 250 | 45 | 5000 | 5000 | 350 | 400 | 500 | 3 + 1 per 2 zones | 0 | all |
| zed | 550 | 500 | 70 | 22000 | none | 900 | 280 | 820 | 2 + 1 per 3 zones | 3 | all |

Regions (money in cents):

| code | zone | no delivery on | haz ban level | duty free up to | duty bp | customs days | remote fee |
|---|---|---|---|---|---|---|---|
| arden | 1 | Sat,Sun | 4 | 15000 | 500 | 1 | 0 |
| brook | 2 | Sat,Sun | 3 | 12000 | 700 | 1 | 150 |
| crest | 3 | Sat,Sun | 2 | 10000 | 800 | 2 | 200 |
| delta | 4 | Sat,Sun | 4 | 8000 | 1000 | 2 | 250 |
| ember | 5 | Sat,Sun | 3 | 8000 | 1200 | 2 | 300 |
| forge | 6 | Fri,Sat | 2 | 6000 | 1500 | 3 | 350 |
| gale | 7 | Sat,Sun | 1 | 5000 | 0 | 0 | 400 |
| haven | 8 | Sat,Sun | 4 | 0 | 900 | 3 | 450 |
| depot | 0 | Sat,Sun | 4 | 0 | 0 | 0 | 0 |

Items (cents):

| sku | category | cost | price |
|---|---|---|---|
| bolt-m6 | fasteners | 8 | 15 |
| screw-w4 | fasteners | 5 | 9 |
| cable-usb | cables | 120 | 290 |
| cable-hdmi | cables | 210 | 480 |
| paper-a4 | paper | 350 | 620 |
| paper-a3 | paper | 610 | 990 |
| hammer-1 | tools | 700 | 1450 |
| wrench-set | tools | 1900 | 3900 |
| plier-9 | tools | 800 | 1700 |
| charger-20 | electronics | 900 | 2200 |
| speaker-bt | electronics | 2400 | 5900 |
| tumbler-6 | glassware | 150 | 390 |
| vase-30 | glassware | 1100 | 2600 |
| shirt-m | apparel | 500 | 1400 |
| jacket-l | apparel | 2300 | 5500 |
| crisps-50 | snacks | 30 | 80 |
| bar-oat | snacks | 25 | 70 |
| milk-1l | dairy | 60 | 120 |
| yogurt-4 | dairy | 140 | 290 |
| apple-1k | produce | 120 | 260 |
| lettuce-1 | produce | 50 | 130 |
| vitamin-c | medicine | 200 | 520 |
| bandage-50 | medicine | 180 | 450 |
| pizza-fr | frozen | 180 | 420 |
| peas-fr | frozen | 90 | 200 |
| thinner-1l | solvents | 400 | 900 |
| cleaner-5l | solvents | 900 | 1900 |
| plank-2m | lumber | 350 | 780 |
| beam-3m | lumber | 900 | 2000 |

Tiers: `basic` rank 2 free freight from 200.00, `silver` rank 1 from 100.00,
`gold` rank 0 from 50.00.

## Special cases

These exceptions are deliberate. They are not mistakes in the modules that
carry them.

Warehouses

1. Cedar is an overflow yard: it may hold up to 10% more than the capacity in
   the table.
2. Juniper charges its pick fee per unit, not per line.
3. Elm's cut-off on Saturdays is 12; the table value applies on the other
   days.
4. Larch counts as distance 0 for the regions forge and gale.
5. A cut-off of 24 (iris) means every order is dispatched the same day it is
   placed; a cut-off of 0 (kelp) means it never is.

Categories

6. Cables are sold loose: receipts are booked exactly as given, with no
   rounding to packs.
7. Fasteners are sold in whole packs only: an order line must be a multiple of
   the pack.
8. Glassware weighs 10% more than its unit weights add up to (packaging),
   rounded half up.
9. Lumber is weighed in whole kilograms: the weight of a line is rounded up to
   the next 1000 g.
10. Medicine carries the expiry day printed on the goods: `receive` needs
    `exp=DAY` (not before today) and the other categories refuse `exp`.
11. Paper is made to order: although the table gives it a reorder point, it
    never shows up in `replenish` or `low_stock`.
12. A category with no return days takes no returns. A category that never
    restocks scraps every return, good or damaged. A category without a line
    limit has no limit.

Carriers

13. Parcelo is a flat-rate carrier (no charge per step). Haul has no parcel
    limit and takes any weight; Pony only takes shipments up to 5000 g in
    total. Tern serves only the regions listed in the table.
14. Aero Express always takes its base transit days, whatever the distance.
15. Nord truncates its fuel surcharge (rounds it down) instead of rounding it.
16. Gull applies its zone and fuel surcharges to the per-parcel base fee only,
    not to the weight charge.
17. Zed applies its minimum charge to the base rate, before the surcharges.

Regions

18. Delta charges duty in two parts of 5% each, each rounded half up on its
    own.
19. Ember rounds duty up to the next cent.
20. Forge has no deliveries on Friday and Saturday (table).
21. Gale charges no duty. In Haven every shipment is dutiable (the duty-free
    amount is 0).
22. Depot is a collection point: nothing is carried, so a shipment to a
    customer in depot has no carrier (`pickup`), no freight, no remote fee and
    no transit.

Accounts and commands

23. A note may be set on a closed account, and changing a note is not written
    to the audit log. Changing the region of an account that has open orders
    is refused. A carrier can only be set if it serves the account's region.
24. Closing an account does not touch its open orders: they can still be
    shipped, cancelled and filled from backorder, and returns are accepted from
    closed accounts. `backorder run` skips accounts that are on hold; `ship`
    does not.
25. Transfers are not limited by the capacity of the receiving warehouse.
26. The free-freight waiver covers the carrier charge and the remote fee only;
    handling and duty are charged anyway.
27. The `cancelled` report lists cancelled orders only and the `status` report
    counts every order. `returns_cat` and `scrap_cat` are read from the
    stock ledger. The `cust=` option of a report accepts any known account.
28. If a customer's carrier preference is a carrier that does not serve the
    region (the region was changed before), the shipment is refused.

## The consistency check

After every command the program verifies that: every lot holds at least one
unit and has no more reserved than it holds; for every warehouse and sku the
ledger adds up to the units in the lots; the reserved quantity of every lot
equals the quantity allocated to orders on it; each order line is accounted
for (ordered = reserved + backordered + shipped + cancelled) and returned
never exceeds shipped; order statuses match their lines; shipments are
numbered without gaps, their quantities add up to what the order lines show
as shipped, and no amount in them is negative.
