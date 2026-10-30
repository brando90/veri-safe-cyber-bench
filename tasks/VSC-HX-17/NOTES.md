# VSC-HX-17 author notes (private)

stockyard: a toy warehouse inventory and order-routing system. 106 Python modules
(6,904 lines in public/src) plus a README. Lever (hard tier v6, "decoy-heavy
variant of the HX-13 shape"): the product is generated-style, one module per
warehouse (12), category (14), carrier (9), region (9), customer setter (9) and
report (16), with table-driven dispatch. There are only K = 8 independent
defects but 51 deliberate exceptions (decoys). About 22 of the decoys look
MORE suspicious than the real defects (a different lookup call than all
siblings, a different rounding helper, an extra or a missing guard, a constant
that deviates from the family). The README documents each exception in its
reference tables or its numbered "Special cases" section. INSTRUCTION.md
tells the solver to keep documented behaviour intact. The tempting wrong move
is to normalise a decoy, which fails ref_tests; the right move needs the
README's special-cases list and the code's dominant convention.

Everything derived is produced deterministically by private/build_private.sh:
gen_gold.py writes private/gold (the generator holds the repetitive modules as
templates; core/ holds the hand-written shared modules and the README source),
make_variants.py derives public/src (gold plus all eight defects, by exact
unique text replacement), the eight mutants and the control patch trees,
make_inputs.py/cases_*.py write every .in file, and every .out file is produced
by running gold. check_variants.py, check_decoys.py (writes DECOYS.md) and
run_controls.py (writes CONTROLS.md) verify it all.

Two look-alike pairs (a defect and a decoy that deviates the same way) are
deliberate: M05 setter email (defect) vs X01 setter note (decoy); M06 tier
report (defect) vs X05 cancelled report (decoy); M03 tern zone base (defect) vs
K05 gull zone base (decoy); M08 apparel pack rounding (defect) vs C01 cables
loose (decoy). A solver who fixes by pattern ("make it like its siblings")
fixes the defect and also breaks the decoy next to it.

## The defects (K = 8, one mutant each in private/mutants)

| Mutant | Module | Defect | Why the correct behaviour is derivable | Guarding ref_edge | Documented? |
|---|---|---|---|---|---|
| M01_snacks_margin | cat_snacks.sellable | `expiry - day > MARGIN` | README: allocated only while expiry minus today is at least the margin; 13 sibling categories use `>=` | e01, e02, e17 | documented |
| M02_birch_cutoff | wh_birch.dispatch_day | `hour <= cutoff_on(day)` | README: leaves the same day if H is before the cut-off hour; the 11 sibling warehouses use `<` | e03, e04, e18 | documented |
| M03_tern_zone_base | car_tern.charge | zone surcharge on `parcels(weight) * BASE` | 8 of 9 carriers compute the zone surcharge on the full rate subtotal `sub`; the only documented exception is gull (special case 16), tern is not | e05, e06, e19 | convention-only |
| M04_brook_hazard_ban | reg_brook.allows | `haz <= BAN_HAZ` | `region show` prints 'refuses hazard class N and above'; README orders paragraph; the other 8 regions use `<` | e07, e08 | documented |
| M05_email_closed | set_email.cmd_set_email | `customers.get` instead of `customers.open` | README: a closed account cannot be changed; special case 23 exempts only the note setter | e09, e10, e19 | documented |
| M06_goods_tier_cancelled | rpt_goods_tier.run | `w.orders.values()` instead of `orders.live(w)` | the sibling reports goods_customer and goods_region (and backorders) walk `orders.live`; the report's own `total_orders` counts live orders; special case 27 names the only two reports that cover cancelled orders (cancelled, status) | e11, e12, e19 | convention-only |
| M07_adjust_reserved | adjust.cmd_adjust | `min(lot.qty, need)` instead of `min(stock.free(lot), need)` | README: units reserved for orders cannot be counted away; `stock.py` and `transfers.py` use `stock.free` | e13, e14 | documented |
| M08_apparel_pack_floor | cat_apparel.round_receive | `units // PACK * PACK` | README: rounded up to the next full pack unless sold loose (cables only, special case 6); 12 categories use `money.ceil_div` | e15, e16, e19 | documented |

Each mutant fails at least two ref_edge cases, no ref_tests case and no smoke
case (CONTROLS.md part (f)); the original fails every ref_edge case and no
ref_tests or smoke case. No comment or docstring in public/ points at a defect
site; the public README contains no statement about the defects themselves, only
ordinary behaviour (the ban-level wording says "its ban level or a higher
hazard class").

Traps: (1) partial fix: the tern and apparel defects are quiet (no
documented rule for tern; apparel rounds only in a receipt), so a solver that
stops at the loud ones scores RC_edge < 1 (control d); the hazard ban boundary
is a one-token change that is easy to dismiss (control d2). (2) over-aggressive
fix: normalising the most suspicious exceptions (controls e, e2) fails
ref_tests. (3) look-alike pairs above.

## Decoys (51)

Every decoy is documented in the README (table or special case). `Susp` marks the ones that look more suspicious than the real defects. The last column lists the ref_tests cases that fail when that decoy alone is normalised (from check_decoys.py; every decoy is guarded by at least one, tidy-six together fail 6 distinct cases).

| id | module | Susp | What looks odd | Documented in | Guarding ref_tests |
|---|---|---|---|---|---|
| W01_iris_cutoff24 | wh_iris.py |  | cut-off hour 24 (every hour is before it) | special case 5 | t04_cutoffs_iris_kelp, t49_catalog_and_help |
| W02_kelp_cutoff0 | wh_kelp.py |  | cut-off hour 0 (nothing is before it) | special case 5 | t04_cutoffs_iris_kelp, t49_catalog_and_help |
| W03_harbor_seven_days | wh_harbor.py |  | opens Sundays, siblings Mon-Fri | table | t06_open_days_harbor_fjord, t31_forge_delivery_days, t49_catalog_and_help |
| W04_cedar_soft_capacity | wh_cedar.py | yes | capacity check allows 10% over the table value | special case 1 | t07_cedar_capacity, t08_transfer_capacity |
| W05_juniper_per_unit | wh_juniper.py | yes | pick fee multiplied by units, siblings by lines | special case 2 | t09_juniper_pick_fee, t25_carrier_tern_pony, t45_seeded_random_a, t46_seeded_random_b |
| W06_elm_saturday | wh_elm.py | yes | extra Saturday branch in the cut-off rule | special case 3 | t05_cutoff_elm_saturday |
| W07_larch_preferred | wh_larch.py |  | distance forced to 0 for two regions | special case 4 | t10_larch_preferred, t46_seeded_random_b |
| W08_fjord_closed_monday | wh_fjord.py |  | dispatch days start on Tuesday | table | t06_open_days_harbor_fjord, t49_catalog_and_help |
| C01_cables_loose | cat_cables.py |  | receipt booked as given, siblings round up to packs | special case 6 | t11_routing_split_backorder, t12_pack_rounding_loose, t38_replenish_low_stock, t45_seeded_random_a, t46_seeded_random_b |
| C02_lumber_kilograms | cat_lumber.py | yes | weight rounded up to 1000 g | special case 9 | t15_lumber_weight, t19_returns_windows, t20_carrier_swift_parcelo_haul, t21_carrier_nord, t22_carrier_aero, t23_carrier_gull, t24_carrier_zed, t25_carrier_tern_pony, t26_auto_carrier_choice, t32_free_freight_tiers, t40_reports_overview, t45_seeded_random_a, t46_seeded_random_b, t48_return_boundaries |
| C03_medicine_given_expiry | cat_medicine.py | yes | expiry comes from the exp= option (required), siblings refuse exp= | special case 10 | t16_medicine_expiry, t17_margins_boundaries, t38_replenish_low_stock, t47_fefo_pick_order |
| C04_dairy_no_returns | cat_dairy.py |  | return window 0 (no returns) | special case 12 | t19_returns_windows, t40_reports_overview |
| C05_produce_never_restocks | cat_produce.py |  | RESTOCK never | special case 12 | t19_returns_windows |
| C06_glassware_padding | cat_glassware.py | yes | weight padded by 10% | special case 8 | t14_glassware_weight, t19_returns_windows, t45_seeded_random_a, t46_seeded_random_b, t48_return_boundaries |
| C07_fasteners_whole_packs | cat_fasteners.py | yes | extra pack-multiple refusal on order lines | special case 7 | t13_line_rules |
| C08_paper_made_to_order | cat_paper.py | yes | reorder point 40 in the table but needs_reorder is constant False | special case 11 | t38_replenish_low_stock, t45_seeded_random_a |
| C09_tools_no_line_limit | cat_tools.py |  | MAX_LINE 0 (no limit) | special case 12 | t13_line_rules, t49_catalog_and_help |
| C10_solvents_never_restock | cat_solvents.py |  | RESTOCK never | special case 12 | t19_returns_windows |
| C11_frozen_margin | cat_frozen.py |  | margin 10 days | table | t17_margins_boundaries, t49_catalog_and_help |
| C12_snacks_never_restock | cat_snacks.py |  | RESTOCK never (sits next to the margin defect module) | special case 12 | t19_returns_windows |
| C13_medicine_margin | cat_medicine.py |  | margin 30 days | table | t16_medicine_expiry, t17_margins_boundaries, t49_catalog_and_help |
| K01_parcelo_flat | car_parcelo.py |  | no charge per weight step | special case 13 | t03_region_guard, t04_cutoffs_iris_kelp, t05_cutoff_elm_saturday, t06_open_days_harbor_fjord, t09_juniper_pick_fee, t14_glassware_weight, t15_lumber_weight, t19_returns_windows, t20_carrier_swift_parcelo_haul, t26_auto_carrier_choice, t34_closed_account_orders, t39_cancelled_report, t40_reports_overview, t41_report_filters, t42_exports, t45_seeded_random_a, t46_seeded_random_b, t49_catalog_and_help |
| K02_haul_no_parcel_limit | car_haul.py |  | no parcel limit | special case 13 | t20_carrier_swift_parcelo_haul, t49_catalog_and_help |
| K03_aero_fixed_transit | car_aero.py | yes | transit ignores distance | special case 14 | t22_carrier_aero |
| K04_nord_truncated_fuel | car_nord.py | yes | fuel surcharge floored with //, siblings use money.pct | special case 15 | t21_carrier_nord |
| K05_gull_base_only | car_gull.py | yes | zone and fuel surcharges on the per-parcel base only (the look-alike of the tern zone defect) | special case 16 | t23_carrier_gull, t26_auto_carrier_choice, t39_cancelled_report, t40_reports_overview, t41_report_filters, t46_seeded_random_b |
| K06_tern_regions | car_tern.py |  | serves only six regions | special case 13 and table | t03_region_guard, t25_carrier_tern_pony, t49_catalog_and_help |
| K07_pony_total_limit | car_pony.py |  | total weight limit 5000 g | special case 13 | t25_carrier_tern_pony, t45_seeded_random_a, t49_catalog_and_help |
| K08_zed_minimum_first | car_zed.py | yes | minimum charge applied before surcharges | special case 17 | t24_carrier_zed, t45_seeded_random_a |
| R01_depot_pickup | shipping.py | yes | zone 0 returns a pickup shipment with no carrier | special case 22 | t25_carrier_tern_pony, t27_depot_pickup |
| R02_delta_split_duty | reg_delta.py | yes | duty in two 5% parts, each rounded | special case 18 | t20_carrier_swift_parcelo_haul, t21_carrier_nord, t22_carrier_aero, t23_carrier_gull, t24_carrier_zed, t28_duty_delta |
| R03_ember_duty_up | reg_ember.py | yes | duty rounded up with ceil_div | special case 19 | t29_duty_ember |
| R04_forge_weekend | reg_forge.py |  | no delivery Fri and Sat | table | t26_auto_carrier_choice, t31_forge_delivery_days, t44_hazard_regions, t49_catalog_and_help |
| R05_gale_no_duty | reg_gale.py |  | duty rate 0 | special case 21 | t03_region_guard, t06_open_days_harbor_fjord, t20_carrier_swift_parcelo_haul, t21_carrier_nord, t22_carrier_aero, t23_carrier_gull, t24_carrier_zed, t25_carrier_tern_pony, t26_auto_carrier_choice, t30_duty_gale_haven_arden, t39_cancelled_report, t40_reports_overview, t44_hazard_regions, t46_seeded_random_b, t49_catalog_and_help |
| R06_haven_all_dutiable | reg_haven.py |  | duty-free amount 0 | special case 21 | t30_duty_gale_haven_arden, t44_hazard_regions, t46_seeded_random_b, t49_catalog_and_help |
| R07_crest_ban_level | reg_crest.py |  | ban level 2 (stricter than siblings) | table | t44_hazard_regions, t49_catalog_and_help |
| X01_note_on_closed | set_note.py | yes | set note uses customers.get, every other setter customers.open (the look-alike of the email defect) | special case 23 | t02_closed_accounts |
| X02_note_not_audited | set_note.py | yes | no audit line for a note change | special case 23 | t01_setters, t02_closed_accounts, t50_parsing_and_errors |
| X03_region_open_orders | set_region.py |  | set region refuses when the account has open orders | special case 23 | t03_region_guard, t45_seeded_random_a |
| X04_carrier_serves_region | set_carrier.py |  | set carrier refuses a carrier that does not serve the region | special case 23 | t03_region_guard |
| X05_cancelled_report_all | rpt_cancelled.py | yes | cancelled report iterates every order (the look-alike of the tier report defect) | special case 27 | t39_cancelled_report |
| X06_return_closed_ok | returns.py | yes | return uses customers.get, accepted for closed accounts | special case 24 | t34_closed_account_orders |
| X07_ship_closed_ok | shipping.py | yes | ship accepted for closed accounts | special case 24 | t34_closed_account_orders |
| X08_cancel_closed_ok | orders.py |  | cancel accepted for closed accounts | special case 24 | t34_closed_account_orders |
| X09_backorder_closed_ok | backorders.py |  | backorder run serves closed accounts | special case 24 | t34_closed_account_orders |
| X10_transfer_capacity_exempt | transfers.py | yes | transfer has no capacity check on the receiving warehouse | special case 25 | t08_transfer_capacity |
| X11_backorder_skips_hold | backorders.py |  | backorder run skips accounts on hold | special case 24 | t33_holds_and_backorder_run |
| X12_ship_ignores_hold | shipping.py |  | ship has no hold check | special case 24 | t33_holds_and_backorder_run |
| X13_free_freight_only_freight | shipping.py | yes | waiver covers carrier charge and remote fee only | special case 26 | t09_juniper_pick_fee, t15_lumber_weight, t19_returns_windows, t20_carrier_swift_parcelo_haul, t25_carrier_tern_pony, t26_auto_carrier_choice, t27_depot_pickup, t32_free_freight_tiers, t33_holds_and_backorder_run, t34_closed_account_orders, t39_cancelled_report, t40_reports_overview, t45_seeded_random_a, t46_seeded_random_b, t48_return_boundaries |
| X14_duplicate_lines_added | orders.py |  | a repeated sku on an order is added up | orders section | t11_routing_split_backorder, t43_refs_duplicates_lines |
| X15_report_cust_closed_ok | reportutil.py |  | cust= filter accepts closed accounts | special case 27 | t41_report_filters |

Tidy-six control (`e_tidy6`): X01, X05, K04, R03, W04, X10 (closed-account note,
cancelled report, nord fuel rounding, ember duty rounding, cedar capacity,
transfer capacity). Second group (`e2_tidy_more`): K05, K08, X06, X07, C07,
W05, X13, R01.

Decoys that deliberately duplicate a documented table entry (no deviation in
code, only a constant): W01-W03, W08, C04-C05, C09-C13, K01-K02, K06-K07,
R04-R07. These are the weaker decoys (a solver that does not touch them loses
nothing); the stronger ones are the structural deviations flagged Susp.

## ref_tests and ref_edge

50 ref_tests (t01-t50) cover every documented exception and the ordinary
behaviour around them: setters, closed accounts, carriers and the automatic
carrier choice, duty rules, cut-off and dispatch days, transfers and capacity,
returns windows, backorder ordering, reports and exports, long seeded random
sessions (t45, t46, t49) and the consistency check. They avoid every defect
(the original passes all of them). 19 ref_edge cases (e01-e19) are specific
scenarios per defect (two or three each, including parameter sweeps and one
mixed scenario) that the original gets wrong.

Weaknesses: see the end of private/CONTROLS.md notes and the author's report.
