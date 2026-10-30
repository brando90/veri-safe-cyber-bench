# Controls (real scorer output, `python3 private/score_task.py <task> private/controls/<name>`)

Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with `sh private/build_private.sh && python3 private/run_controls.py`.

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |
|---|---|---|---|---|---|---|
| a_original | 0.0 | 0.0 | 0.0 | 0.84 | 0.0 | (a) unpatched source as patch, plus one correct test. ref_tests failed: t05_alerts_all_kinds, t10_import_roundtrip, t19_errors, t21_big_stream; ref_edge failed: e01_cap_zero_on_ship, e02_cap_zero_global, e03_alert_hold_exact, e04_alert_override_open, e05_sla_reading_at_close, e06_sla_close_in_band_many, e07_legs_full_journey, e08_legs_partial, e09_skew_positive, e10_skew_negative, e11_export_backslash_label, e12_export_import_cycle, e13_rank_ties_displayed, e14_rank_ties_many, e15_find_decomposed_query, e16_find_blank_runs, e17_offset_above_range, e18_offset_load_path; mutants killed: 0/9 |
| b_gold | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | (b) gold as patch; every ref_edge plus two ref_tests as agent tests. ref_tests failed: -; ref_edge failed: -; mutants killed: 9/9 |
| c_empty | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | (c) empty out/. ref_tests failed: -; ref_edge failed: -; mutants killed: 0/9 |
| d_partial | 1.0 | 1.0 | 0.7778 | 1.0 | 0.7778 | (d) every defect fixed except the rank tie precision and the clamp order; one test per fixed defect. ref_tests failed: -; ref_edge failed: e13_rank_ties_displayed, e14_rank_ties_many, e17_offset_above_range, e18_offset_load_path; mutants killed: 7/9 |
| e_overaggressive | 1.0 | 0.0 | 0.1111 | 0.8 | 0.9444 | (e) gold plus over-fixing: prune drops a reading at the cutoff, user ranges stop before the end, labels collapse every whitespace character, delays round down, averages use round(). ref_tests failed: t02_window_ranges, t09_prune_keep, t17_plans_delay, t21_big_stream, t25_describe_compare; ref_edge failed: e10_skew_negative; mutants killed: 1/9 |
| e2_wrong_side | 0.0 | 0.0 | 0.2222 | 0.56 | 0.6111 | (e2) six symptoms repaired on the other side of the boundary (the owner module changed instead of the adapting one); tests are the correct outputs for the symptoms. ref_tests failed: t01_setup_show, t02_window_ranges, t04_excursions, t05_alerts_all_kinds, t07_sla_journeys, t09_prune_keep, t10_import_roundtrip, t11_shift, t17_plans_delay, t21_big_stream, t23_site_export; ref_edge failed: e01_cap_zero_on_ship, e02_cap_zero_global, e03_alert_hold_exact, e04_alert_override_open, e05_sla_reading_at_close, e07_legs_full_journey, e17_offset_above_range; mutants killed: 2/9 |
| p1_find_nfc_only | 1.0 | 1.0 | 0.1111 | 0.96 | 0.9444 | (p1) query defect repaired for Unicode normalisation only, blank runs stay. ref_tests failed: t19_errors; ref_edge failed: e16_find_blank_runs; mutants killed: 1/9 |

## (f) Mutants against smoke and ref_edge

Each mutant is gold with exactly one defect brought back (`python3 private/check_variants.py` gives the same data plus ref_tests).

| Mutant | smoke failed | ref_edge failed |
|---|---|---|
| M01_cap_zero | none | e01_cap_zero_on_ship, e02_cap_zero_global |
| M02_hold_units | none | e03_alert_hold_exact, e04_alert_override_open |
| M03_journey_end | none | e05_sla_reading_at_close, e06_sla_close_in_band_many |
| M04_stop_base | none | e07_legs_full_journey, e08_legs_partial |
| M05_skew_sign | none | e09_skew_positive, e10_skew_negative, e12_export_import_cycle |
| M06_label_escape | none | e11_export_backslash_label, e12_export_import_cycle |
| M07_tie_precision | none | e13_rank_ties_displayed, e14_rank_ties_many |
| M08_query_clean | none | e15_find_decomposed_query, e16_find_blank_runs |
| M09_clamp_order | none | e17_offset_above_range, e18_offset_load_path |

## Raw scorer output

### a_original

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.84, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_cap_zero_on_ship"], "agent_tests_fail_on_patch": ["e01_cap_zero_on_ship"], "mutants_killed": {"M01_cap_zero": false, "M02_hold_units": false, "M03_journey_end": false, "M04_stop_base": false, "M05_skew_sign": false, "M06_label_escape": false, "M07_tie_precision": false, "M08_query_clean": false, "M09_clamp_order": false}, "patch_build": "ok", "ref_edge_failed": ["e01_cap_zero_on_ship", "e02_cap_zero_global", "e03_alert_hold_exact", "e04_alert_override_open", "e05_sla_reading_at_close", "e06_sla_close_in_band_many", "e07_legs_full_journey", "e08_legs_partial", "e09_skew_positive", "e10_skew_negative", "e11_export_backslash_label", "e12_export_import_cycle", "e13_rank_ties_displayed", "e14_rank_ties_many", "e15_find_decomposed_query", "e16_find_blank_runs", "e17_offset_above_range", "e18_offset_load_path"], "ref_tests_failed": ["t05_alerts_all_kinds", "t10_import_roundtrip", "t19_errors", "t21_big_stream"], "smoke_pass": true}}
```

### b_gold

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_tests": 20, "agent_tests_fail_on_original": ["e01_cap_zero_on_ship", "e02_cap_zero_global", "e03_alert_hold_exact", "e04_alert_override_open", "e05_sla_reading_at_close", "e06_sla_close_in_band_many", "e07_legs_full_journey", "e08_legs_partial", "e09_skew_positive", "e10_skew_negative", "e11_export_backslash_label", "e12_export_import_cycle", "e13_rank_ties_displayed", "e14_rank_ties_many", "e15_find_decomposed_query", "e16_find_blank_runs", "e17_offset_above_range", "e18_offset_load_path"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_cap_zero": true, "M02_hold_units": true, "M03_journey_end": true, "M04_stop_base": true, "M05_skew_sign": true, "M06_label_escape": true, "M07_tie_precision": true, "M08_query_clean": true, "M09_clamp_order": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": true}}
```

### c_empty

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_tests": 0, "agent_tests_fail_on_original": [], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_cap_zero": false, "M02_hold_units": false, "M03_journey_end": false, "M04_stop_base": false, "M05_skew_sign": false, "M06_label_escape": false, "M07_tie_precision": false, "M08_query_clean": false, "M09_clamp_order": false}, "patch_build": "missing tree", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": false}}
```

### d_partial

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.7778, "RC_tests": 1.0, "VC": 0.7778, "details": {"agent_tests": 7, "agent_tests_fail_on_original": ["e01_cap_zero_on_ship", "e03_alert_hold_exact", "e05_sla_reading_at_close", "e07_legs_full_journey", "e09_skew_positive", "e11_export_backslash_label", "e15_find_decomposed_query"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_cap_zero": true, "M02_hold_units": true, "M03_journey_end": true, "M04_stop_base": true, "M05_skew_sign": true, "M06_label_escape": true, "M07_tie_precision": false, "M08_query_clean": true, "M09_clamp_order": false}, "patch_build": "ok", "ref_edge_failed": ["e13_rank_ties_displayed", "e14_rank_ties_many", "e17_offset_above_range", "e18_offset_load_path"], "ref_tests_failed": [], "smoke_pass": true}}
```

### e_overaggressive

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.9444, "RC_tests": 0.8, "VC": 0.1111, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e03_alert_hold_exact"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_cap_zero": false, "M02_hold_units": true, "M03_journey_end": false, "M04_stop_base": false, "M05_skew_sign": false, "M06_label_escape": false, "M07_tie_precision": false, "M08_query_clean": false, "M09_clamp_order": false}, "patch_build": "ok", "ref_edge_failed": ["e10_skew_negative"], "ref_tests_failed": ["t02_window_ranges", "t09_prune_keep", "t17_plans_delay", "t21_big_stream", "t25_describe_compare"], "smoke_pass": false}}
```

### e2_wrong_side

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.6111, "RC_tests": 0.56, "VC": 0.2222, "details": {"agent_tests": 6, "agent_tests_fail_on_original": ["e01_cap_zero_on_ship", "e03_alert_hold_exact", "e05_sla_reading_at_close", "e07_legs_full_journey", "e09_skew_positive", "e11_export_backslash_label"], "agent_tests_fail_on_patch": ["e01_cap_zero_on_ship", "e03_alert_hold_exact", "e05_sla_reading_at_close", "e07_legs_full_journey"], "mutants_killed": {"M01_cap_zero": false, "M02_hold_units": false, "M03_journey_end": false, "M04_stop_base": false, "M05_skew_sign": true, "M06_label_escape": true, "M07_tie_precision": false, "M08_query_clean": false, "M09_clamp_order": false}, "patch_build": "ok", "ref_edge_failed": ["e01_cap_zero_on_ship", "e02_cap_zero_global", "e03_alert_hold_exact", "e04_alert_override_open", "e05_sla_reading_at_close", "e07_legs_full_journey", "e17_offset_above_range"], "ref_tests_failed": ["t01_setup_show", "t02_window_ranges", "t04_excursions", "t05_alerts_all_kinds", "t07_sla_journeys", "t09_prune_keep", "t10_import_roundtrip", "t11_shift", "t17_plans_delay", "t21_big_stream", "t23_site_export"], "smoke_pass": false}}
```

### p1_find_nfc_only

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.9444, "RC_tests": 0.96, "VC": 0.1111, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e15_find_decomposed_query"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_cap_zero": false, "M02_hold_units": false, "M03_journey_end": false, "M04_stop_base": false, "M05_skew_sign": false, "M06_label_escape": false, "M07_tie_precision": false, "M08_query_clean": true, "M09_clamp_order": false}, "patch_build": "ok", "ref_edge_failed": ["e16_find_blank_runs"], "ref_tests_failed": ["t19_errors"], "smoke_pass": true}}
```

