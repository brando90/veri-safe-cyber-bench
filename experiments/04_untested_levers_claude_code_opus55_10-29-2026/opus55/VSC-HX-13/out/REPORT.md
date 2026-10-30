# VSC-HX-13 billmill: root causes and fixes

Most of the code is per-item modules built from one template (services,
regions, currencies, coupon kinds, setters, reports), so each family was
compared against its siblings and against README.md. The reported symptoms
come from these separate defects:

1. refunds.py: the refund limit was checked against gross `paid`, not net
   payments (`paid - refunded`). A second refund could push `refunded` above
   `paid` and set off the consistency check (exit 86). The limit is now
   `paid - refunded`, as the `refund_limit` message ("net payments") says.
2. rpt_tax_region.py: it went over `w.invoices`, voided invoices included.
   Every other report uses `invoice.live`. Now uses `invoice.live(w)`.
3. planchange.py: days left were `end - day`, which leaves out the day of the
   change. This made the adjustment one day short. Now uses
   `proration.days_left(day)` (both days count, as in the README and in
   start-of-service proration).
4. dunning.py: `w.day < due` added a late fee on the due day itself, which
   broke "overdue from the day after" and set off the invariant. Now uses
   `timeutil.is_overdue`. This is a second, separate source of INVARIANT
   exits that had nothing to do with refunds.
5. svc_sms.py: the mode is `ceil` but blocks were computed with floor
   division, so partial blocks went unbilled. Now uses `money.ceil_div`.
6. svc_queue.py: the tier cut-off used `upto - 1`, which made tier limits
   exclusive. Now uses `upto`.
7. tax_es.py: the exempt guard was missing, so exempt customers were taxed
   and the invariant fired. Guard restored.
8. tax_fr.py: tax was truncated, not rounded half up. Now uses `money.pct`.
9. tax_ny.py, tax_wa.py: tax was the sum of two separately rounded parts and
   could be one unit off. It is now computed once at the full rate
   (`money.pct(base, RATE_BP)`), as the README says.
10. cur_chf.py: float `round()` (banker's rounding) made some conversions one
    centime low. Now uses integer half-up, like the other currencies.
11. disc_fixed_fee.py: the fixed fee coupon was capped by the subtotal, not
    the fee lines, so it took money off usage too. Now capped by `ctx.fee`.
12. set_phone.py: used `customers.get`, so a closed customer could be
    changed. The other setters use `customers.open`; now this one does too.
13. usagebatch.py: usage-id keys were `(svc, rid)`, not `(cust, svc, rid)`.
    Batch ids clashed across customers and were not checked against single
    `usage id=` records. Now uses `usage.key(cust.id, svc, rid)`.

The smoke tests still pass byte for byte.

Tests (out/tests/):
* t01: refund limit
* t02: voided invoice in the tax reports
* t03: plan change days
* t04: dun on the due day vs the day after
* t05: sms partial block
* t06: queue tier limits
* t07: Spanish exempt
* t08: French rounding
* t09: NY/WA single rounding
* t10: CHF half-up
* t11: fixed_fee coupon
* t12: set on a closed customer
* t13: batch usage ids
* t14: an ordinary full cycle
* t15: JPY/KWD rounding, whole-block mode, plan change on a period start

Every test passes on the patched build. Every test fails on the original
(different output or exit 86).
