# VSC-HX-17 stockyard: root causes and fixes

Every module was checked against the README (the reference tables and the special cases).
Sibling modules were diffed against each other, and the shared helpers were read in full.
I found eight defects. Each one is a single line in one module. All documented exceptions
(cedar overflow, juniper per-unit pick, elm Saturday cut-off, larch distance, iris/kelp
cut-offs, cables loose, fasteners packs, glassware padding, lumber kg, medicine exp, paper
never reorders, parcelo/haul/pony/aero/nord/gull/zed rules, delta/ember/gale/haven/depot,
the note exception for closed accounts) are left as they were.

| # | file | defect | fix |
|---|---|---|---|
| 1 | `set_email.py` | looked the account up with `customers.get`, so a closed account could still have its email changed (and audited) | use `customers.open`, which refuses closed accounts like the other setters (the note setter stays on `get`, as documented) |
| 2 | `rpt_goods_tier.py` | summed `w.orders.values()`, which includes cancelled orders | sum `orders.live(w)` like `goods_region` and `goods_customer` |
| 3 | `wh_birch.py` | cut-off test was `hour <= cutoff`, so goods ready at 15:00 were dispatched the same day | `hour < cutoff`, the rule in the README |
| 4 | `cat_apparel.py` | receipts rounded DOWN to packs (`units // PACK * PACK`), so receipts were booked short; receipts under one pack made a 0-unit lot and an INVARIANT failure | round up to whole packs (`ceil_div`) |
| 5 | `cat_snacks.py` | sellable test was `expiry - day > MARGIN`, which refused lots with exactly the margin days left | `>= MARGIN`, the README rule |
| 6 | `car_tern.py` | zone surcharge was taken on the per-parcel base fee only (Gull's documented exception, copied by mistake) | zone surcharge on the full rate, like the other carriers |
| 7 | `reg_brook.py` | `allows` was `haz <= BAN_HAZ`, so Brook accepted goods of its own ban level (solvents, class 3) | `haz < BAN_HAZ` |
| 8 | `adjust.py` | a negative adjustment took `min(lot.qty, need)` from each lot, so reserved units were counted away. This left lots holding fewer units than reserved and failed the INVARIANT check | take only the free units `min(stock.free(lot), need)` from each lot in pick order |

## Tests (out/tests)

* `t01_closed_email`: email refused on a closed account. Note is still allowed there, and po is refused.
* `t02_goods_tier_cancelled`: goods_tier leaves out cancelled orders and agrees with goods_region and goods_customer.
* `t03_birch_cutoff`: Birch at 14 dispatches the same day. At 15 and 16, and at the cut-off on a Friday, it dispatches the next open day.
* `t04_apparel_packs`: apparel receipts round up. Tools, cables and replenish are unchanged.
* `t05_snacks_margin`: a snacks lot with exactly 14 days left is still allocated, and one with 13 days left is not.
* `t06_tern_charge`: Tern freight with the zone surcharge on the full rate. Swift is shown for comparison.
* `t07_brook_hazard`: Brook refuses class 3 and accepts class 1. Delta and crest are unchanged.
* `t08_adjust_reserved`: a negative count skips reserved units and the order still ships. The positive count goes to the newest lot.
* `t09_dispatch_rules`: kept documented behaviour, namely Elm's Saturday cut-off of 12, Iris at 24 and Kelp at 0.

Tests t01 to t08 all give different output on the original program. t04 and t08 also end with exit status 86 there.
