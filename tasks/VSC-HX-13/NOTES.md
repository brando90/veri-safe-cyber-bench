# VSC-HX-13 author notes (private)

billmill: toy usage-metering and invoicing engine. 109 Python modules (7,177
lines in public/src) plus a README. Lever (hard tier v5, "too large to read
in one pass"): the repetitive parts of the product are one module per item
(18 services, 11 tax regions, 8 coupon kinds, 8 currencies, 9 customer
setters, 14 reports, table-driven command dispatch), so a solver cannot read
everything and has to find the odd one out among near-identical siblings by
diffing/grepping, then fix it in the way the rest of the code (and the README
for about half of the defects) says. The generator for the repetitive modules
is private/gen_gold.py (its output is committed as plain source in
private/gold and public/src); make_variants.py derives public/src and the
mutants by exact, unique text replacement.

The README documents ordinary behaviour, not the defects. It states the rule
for D01, D02, D03, D07, D08, D09 (partial blocks round up except in mode
`whole`, tier limits inclusive, exempt customers never taxed, closed
customers cannot be changed, overdue starts the day after the due day, days
left are inclusive). D04, D05, D06, D10, D11, D12 are convention-only.
No comment or docstring in public/ points at a defect site.

## The defects (K = 12, one mutant each in private/mutants)

| Mutant | Module | Defect | Why the correct behaviour is derivable |
|---|---|---|---|
| M01_sms_blocks | svc_sms.blocks_for | `billable // BLOCK` (floor) | 15 of 18 services round up with `money.ceil_div`; README rule; only `whole`-mode services (voice, ocr, geocode) floor on purpose. |
| M02_queue_tier | svc_queue.tier_spans | `min(blocks, upto - 1)` | Every other service uses `min(blocks, upto)`; README: tier limits are inclusive. |
| M03_es_exempt | tax_es.compute | no `if exempt: return 0` guard | All other regions have it; README rule; invariant (exit 86). |
| M04_fr_rounding | tax_fr.compute | `base * RATE_BP // 10000` (truncate) | All other regions use `money.pct` (half up); README: tax rounded to a whole minor unit (same helper as late fee and proration). |
| M05_fixed_fee_cap | disc_fixed_fee.amount | `min(cp.value, ctx.subtotal)` | Siblings cap a fixed amount at the total its TARGET names (`fixed_all` subtotal, `fixed_usage` usage); `fixed_fee` must cap at `ctx.fee`. |
| M06_chf_rounding | cur_chf.from_base | `int(round(x / 1e6))` (half even) | The other seven currencies use `(cents * RATE_PPM + 500000) // 1000000` (half up). Needs a line whose converted value is exactly .5 (e.g. 45 base cents -> 40.5). |
| M07_phone_closed | set_phone.cmd_set_phone | `customers.get` | The other eight setters use `customers.open`; README: a closed customer cannot be changed. |
| M08_dun_boundary | dunning.cmd_dun | `w.day < inv.due` (due day counts as overdue) | `timeutil.is_overdue` (`today > due`); README rule; invariant (late_day > due), exit 86. |
| M09_plan_days | planchange.cmd_set | `end(period) - day` | `proration.days_left` (inclusive); README rule; first-invoice proration uses it. |
| M10_refund_cap | refunds.cmd_refund | `amount > inv.paid` | Must be `inv.paid - inv.refunded`; the invariant requires `refunded <= paid` (exit 86 on a second refund). |
| M11_tax_report_void | rpt_tax_region.run | iterates `w.invoices.values()` | The other grouped reports iterate `invoice.live(w)`. Decoy: `rpt_voided` deliberately lists all invoices. |
| M12_batch_key | usagebatch.cmd_batch | key `(svc, rid)` | `usage.key(cust, svc, rid)` is the key everywhere else; the same prefix for two customers is refused, and a batch id can slip past a single record's id. |

## Decoys (must keep working)

whole-mode services (floor), minimum-charge services (dns, cache),
zero-allowance services, split-rate regions (ny, wa), usage-only tax (jp),
no-usage tax (ch), late fees not taxed, `customers.get` used by read-only
commands and by refunds (refunds are allowed on closed customers),
`rpt_voided` and the ledger-based reports not using `invoice.live`, credit use
recorded as a ledger credit_use entry, an inline CHF-like formula that equals
the shared half-up form in the other currencies, a redundant
`fee if days == PERIOD else share` branch, dead `legacy.py`.

## Hidden tests

private/ref_tests (26): ordinary behaviour, including the decoys and a seeded
about-500-command script that avoids every defect trigger; the original passes
all of them. private/ref_edge (27): each fails on the original; e01..e24 are
two cases per defect, e25-e27 are sweeps over services, regions and currencies.
Smoke (5 cases) shows normal behaviour only.

Rebuild: `sh private/build_private.sh && python3 private/check_variants.py &&
python3 private/run_controls.py` (writes CONTROLS.md; run_controls takes about
4 minutes for 8 scorer runs plus the mutant sweep; one scorer run about 30 s).
