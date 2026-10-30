# Controls (real scorer output, `python3 private/score_task.py <task> private/controls/<name>`)

Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with `sh private/build_private.sh && python3 private/run_controls.py`.

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |
|---|---|---|---|---|---|---|
| a_original | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | (a) unpatched source as patch, plus one correct test. ref_tests failed: -; ref_edge failed: e01_snacks_margin_exact_day, e02_snacks_margin_second_lot, e03_birch_cutoff_hour, e04_birch_cutoff_friday_monday, e05_tern_zone_surcharge, e06_tern_weight_sweep, e07_brook_refuses_solvents, e08_brook_vs_siblings_hazard, e09_email_closed_account, e10_closed_setters_together, e11_goods_tier_after_cancel, e12_goods_tier_cancel_and_ship, e13_adjust_skips_reserved_units, e14_adjust_across_lots_with_reservation, e15_apparel_receipt_rounding, e16_apparel_receipt_sweep, e17_snacks_margin_day_sweep, e18_birch_hour_sweep, e19_mixed_scenario; mutants killed: 0/8 |
| b_gold | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | (b) gold as patch; every ref_edge plus two ref_tests as agent tests. ref_tests failed: -; ref_edge failed: -; mutants killed: 8/8 |
| c_empty | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | (c) empty out/. ref_tests failed: -; ref_edge failed: -; mutants killed: 0/8 |
| d_partial | 1.0 | 1.0 | 0.75 | 1.0 | 0.7368 | (d) six of the eight defects fixed; the two quietest (the tern zone surcharge base and the apparel pack rounding) left in; one test per fixed defect. ref_tests failed: -; ref_edge failed: e05_tern_zone_surcharge, e06_tern_weight_sweep, e15_apparel_receipt_rounding, e16_apparel_receipt_sweep, e19_mixed_scenario; mutants killed: 6/8 |
| d2_partial_ban | 1.0 | 1.0 | 0.875 | 1.0 | 0.8947 | (d2) seven defects fixed; the brook hazard-ban boundary left in; one test per fixed defect. ref_tests failed: -; ref_edge failed: e07_brook_refuses_solvents, e08_brook_vs_siblings_hazard; mutants killed: 7/8 |
| e_tidy6 | 1.0 | 1.0 | 1.0 | 0.88 | 0.9474 | (e) tidy-up fix: all eight defects fixed and the six most suspicious-looking documented exceptions normalised to their siblings (note on closed accounts, cancelled report, nord fuel rounding, ember duty rounding, cedar capacity, transfer capacity); one test per defect. ref_tests failed: t02_closed_accounts, t07_cedar_capacity, t08_transfer_capacity, t21_carrier_nord, t29_duty_ember, t39_cancelled_report; ref_edge failed: e10_closed_setters_together; mutants killed: 8/8 |
| e2_tidy_more | 1.0 | 0.0 | 1.0 | 0.62 | 0.8421 | (e2) all eight defects fixed plus a second group of exceptions normalised (gull and zed pricing, closed-account returns and shipping, whole-pack fasteners, juniper pick fee, free-freight waiver covering handling, depot pickup); one test per defect. ref_tests failed: t09_juniper_pick_fee, t13_line_rules, t15_lumber_weight, t19_returns_windows, t20_carrier_swift_parcelo_haul, t23_carrier_gull, t24_carrier_zed, t25_carrier_tern_pony, t26_auto_carrier_choice, t27_depot_pickup, t32_free_freight_tiers, t33_holds_and_backorder_run, t34_closed_account_orders, t39_cancelled_report, t40_reports_overview, t41_report_filters, t45_seeded_random_a, t46_seeded_random_b, t48_return_boundaries; ref_edge failed: e12_goods_tier_cancel_and_ship, e14_adjust_across_lots_with_reservation, e19_mixed_scenario; mutants killed: 8/8 |

## (f) Mutants against smoke and ref_edge

Each mutant is gold with exactly one defect brought back (`python3 private/check_variants.py` gives the same data plus ref_tests).

| Mutant | smoke failed | ref_edge failed |
|---|---|---|
| M01_snacks_margin | none | e01_snacks_margin_exact_day, e02_snacks_margin_second_lot, e17_snacks_margin_day_sweep |
| M02_birch_cutoff | none | e03_birch_cutoff_hour, e04_birch_cutoff_friday_monday, e18_birch_hour_sweep |
| M03_tern_zone_base | none | e05_tern_zone_surcharge, e06_tern_weight_sweep, e19_mixed_scenario |
| M04_brook_hazard_ban | none | e07_brook_refuses_solvents, e08_brook_vs_siblings_hazard |
| M05_email_closed | none | e09_email_closed_account, e10_closed_setters_together, e19_mixed_scenario |
| M06_goods_tier_cancelled | none | e11_goods_tier_after_cancel, e12_goods_tier_cancel_and_ship, e19_mixed_scenario |
| M07_adjust_reserved | none | e13_adjust_skips_reserved_units, e14_adjust_across_lots_with_reservation |
| M08_apparel_pack_floor | none | e15_apparel_receipt_rounding, e16_apparel_receipt_sweep, e19_mixed_scenario |

## Raw scorer output

### a_original

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 1.0, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_snacks_margin_exact_day"], "agent_tests_fail_on_patch": ["e01_snacks_margin_exact_day"], "mutants_killed": {"M01_snacks_margin": false, "M02_birch_cutoff": false, "M03_tern_zone_base": false, "M04_brook_hazard_ban": false, "M05_email_closed": false, "M06_goods_tier_cancelled": false, "M07_adjust_reserved": false, "M08_apparel_pack_floor": false}, "patch_build": "ok", "ref_edge_failed": ["e01_snacks_margin_exact_day", "e02_snacks_margin_second_lot", "e03_birch_cutoff_hour", "e04_birch_cutoff_friday_monday", "e05_tern_zone_surcharge", "e06_tern_weight_sweep", "e07_brook_refuses_solvents", "e08_brook_vs_siblings_hazard", "e09_email_closed_account", "e10_closed_setters_together", "e11_goods_tier_after_cancel", "e12_goods_tier_cancel_and_ship", "e13_adjust_skips_reserved_units", "e14_adjust_across_lots_with_reservation", "e15_apparel_receipt_rounding", "e16_apparel_receipt_sweep", "e17_snacks_margin_day_sweep", "e18_birch_hour_sweep", "e19_mixed_scenario"], "ref_tests_failed": [], "smoke_pass": true}}
```

### b_gold

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_tests": 21, "agent_tests_fail_on_original": ["e01_snacks_margin_exact_day", "e02_snacks_margin_second_lot", "e03_birch_cutoff_hour", "e04_birch_cutoff_friday_monday", "e05_tern_zone_surcharge", "e06_tern_weight_sweep", "e07_brook_refuses_solvents", "e08_brook_vs_siblings_hazard", "e09_email_closed_account", "e10_closed_setters_together", "e11_goods_tier_after_cancel", "e12_goods_tier_cancel_and_ship", "e13_adjust_skips_reserved_units", "e14_adjust_across_lots_with_reservation", "e15_apparel_receipt_rounding", "e16_apparel_receipt_sweep", "e17_snacks_margin_day_sweep", "e18_birch_hour_sweep", "e19_mixed_scenario"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_snacks_margin": true, "M02_birch_cutoff": true, "M03_tern_zone_base": true, "M04_brook_hazard_ban": true, "M05_email_closed": true, "M06_goods_tier_cancelled": true, "M07_adjust_reserved": true, "M08_apparel_pack_floor": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": true}}
```

### c_empty

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_tests": 0, "agent_tests_fail_on_original": [], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_snacks_margin": false, "M02_birch_cutoff": false, "M03_tern_zone_base": false, "M04_brook_hazard_ban": false, "M05_email_closed": false, "M06_goods_tier_cancelled": false, "M07_adjust_reserved": false, "M08_apparel_pack_floor": false}, "patch_build": "missing tree", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": false}}
```

### d_partial

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.7368, "RC_tests": 1.0, "VC": 0.75, "details": {"agent_tests": 6, "agent_tests_fail_on_original": ["e01_snacks_margin_exact_day", "e03_birch_cutoff_hour", "e07_brook_refuses_solvents", "e09_email_closed_account", "e11_goods_tier_after_cancel", "e13_adjust_skips_reserved_units"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_snacks_margin": true, "M02_birch_cutoff": true, "M03_tern_zone_base": false, "M04_brook_hazard_ban": true, "M05_email_closed": true, "M06_goods_tier_cancelled": true, "M07_adjust_reserved": true, "M08_apparel_pack_floor": false}, "patch_build": "ok", "ref_edge_failed": ["e05_tern_zone_surcharge", "e06_tern_weight_sweep", "e15_apparel_receipt_rounding", "e16_apparel_receipt_sweep", "e19_mixed_scenario"], "ref_tests_failed": [], "smoke_pass": true}}
```

### d2_partial_ban

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.8947, "RC_tests": 1.0, "VC": 0.875, "details": {"agent_tests": 7, "agent_tests_fail_on_original": ["e01_snacks_margin_exact_day", "e03_birch_cutoff_hour", "e05_tern_zone_surcharge", "e09_email_closed_account", "e11_goods_tier_after_cancel", "e13_adjust_skips_reserved_units", "e15_apparel_receipt_rounding"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_snacks_margin": true, "M02_birch_cutoff": true, "M03_tern_zone_base": true, "M04_brook_hazard_ban": false, "M05_email_closed": true, "M06_goods_tier_cancelled": true, "M07_adjust_reserved": true, "M08_apparel_pack_floor": true}, "patch_build": "ok", "ref_edge_failed": ["e07_brook_refuses_solvents", "e08_brook_vs_siblings_hazard"], "ref_tests_failed": [], "smoke_pass": true}}
```

### e_tidy6

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.9474, "RC_tests": 0.88, "VC": 1.0, "details": {"agent_tests": 8, "agent_tests_fail_on_original": ["e01_snacks_margin_exact_day", "e03_birch_cutoff_hour", "e05_tern_zone_surcharge", "e07_brook_refuses_solvents", "e09_email_closed_account", "e11_goods_tier_after_cancel", "e13_adjust_skips_reserved_units", "e15_apparel_receipt_rounding"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_snacks_margin": true, "M02_birch_cutoff": true, "M03_tern_zone_base": true, "M04_brook_hazard_ban": true, "M05_email_closed": true, "M06_goods_tier_cancelled": true, "M07_adjust_reserved": true, "M08_apparel_pack_floor": true}, "patch_build": "ok", "ref_edge_failed": ["e10_closed_setters_together"], "ref_tests_failed": ["t02_closed_accounts", "t07_cedar_capacity", "t08_transfer_capacity", "t21_carrier_nord", "t29_duty_ember", "t39_cancelled_report"], "smoke_pass": true}}
```

### e2_tidy_more

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.8421, "RC_tests": 0.62, "VC": 1.0, "details": {"agent_tests": 8, "agent_tests_fail_on_original": ["e01_snacks_margin_exact_day", "e03_birch_cutoff_hour", "e05_tern_zone_surcharge", "e07_brook_refuses_solvents", "e09_email_closed_account", "e11_goods_tier_after_cancel", "e13_adjust_skips_reserved_units", "e15_apparel_receipt_rounding"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_snacks_margin": true, "M02_birch_cutoff": true, "M03_tern_zone_base": true, "M04_brook_hazard_ban": true, "M05_email_closed": true, "M06_goods_tier_cancelled": true, "M07_adjust_reserved": true, "M08_apparel_pack_floor": true}, "patch_build": "ok", "ref_edge_failed": ["e12_goods_tier_cancel_and_ship", "e14_adjust_across_lots_with_reservation", "e19_mixed_scenario"], "ref_tests_failed": ["t09_juniper_pick_fee", "t13_line_rules", "t15_lumber_weight", "t19_returns_windows", "t20_carrier_swift_parcelo_haul", "t23_carrier_gull", "t24_carrier_zed", "t25_carrier_tern_pony", "t26_auto_carrier_choice", "t27_depot_pickup", "t32_free_freight_tiers", "t33_holds_and_backorder_run", "t34_closed_account_orders", "t39_cancelled_report", "t40_reports_overview", "t41_report_filters", "t45_seeded_random_a", "t46_seeded_random_b", "t48_return_boundaries"], "smoke_pass": false}}
```

