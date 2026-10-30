# Controls (real scorer output, `python3 private/score_task.py <task> private/controls/<name>`)

Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with `sh private/build_private.sh && python3 private/run_controls.py`.

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |
|---|---|---|---|---|---|---|
| a_original | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | (a) unpatched source as patch, plus one correct test. ref_tests failed: -; ref_edge failed: e01_equals_in_values, e02_equals_strict_keep, e03_prefix_strict_keep, e04_prefix_rule_names, e05_mask_lengths, e06_mask_short_in_message, e07_scrub_many_occurrences, e08_scrub_letter_case, e09_two_prefix_rules, e10_three_prefix_rules, e11_limit_zero, e12_limit_zero_and_equal, e13_purge_run_of_old, e14_purge_after_clock_moves, e15_keep_for_one_export, e16_keep_repeated, e17_share_sixteenths, e18_share_eightieths, e19_rank_ties_sources, e20_rank_ties_users_domains, e21_interplay_fields, e22_interplay_message, e23_interplay_report, e24_interplay_policy, e25_generated_hazards_a, e26_generated_hazards_b, e27_generated_hazards_c; mutants killed: 0/10 |
| b_gold | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | (b) gold as patch; every ref_edge plus two ref_tests as agent tests. ref_tests failed: -; ref_edge failed: -; mutants killed: 10/10 |
| c_empty | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | (c) empty out/. ref_tests failed: -; ref_edge failed: -; mutants killed: 0/10 |
| d_partial | 1.0 | 1.0 | 0.8 | 1.0 | 0.7407 | (d) every slip fixed except the temporary export policy copy and the share formatting; one test per fixed slip. ref_tests failed: -; ref_edge failed: e15_keep_for_one_export, e16_keep_repeated, e17_share_sixteenths, e18_share_eightieths, e23_interplay_report, e24_interplay_policy, e27_generated_hazards_c; mutants killed: 8/10 |
| e_overaggressive | 1.0 | 0.0 | 0.3 | 0.8889 | 0.9259 | (e) gold plus 'hardening' of boundaries that are correct: retention drops a record exactly at the limit, the window includes a record exactly one window old, the average rounds halves up. ref_tests failed: t10_retention_bounds, t12_windows, t14_average_even; ref_edge failed: e18_share_eightieths, e23_interplay_report; mutants killed: 3/10 |
| e2_overaggressive_ids | 1.0 | 0.0 | 0.3 | 0.7407 | 0.7407 | (e2) gold plus 'hardening': leading # removed once only, an empty bytes value rejected, days ahead rounded down, the domain taken after the first @. ref_tests failed: t08_rejects, t13_future_days, t17_domains, t18_show_ids, t21_bytes_and_largest, t25_generated_ordinary_1, t26_generated_ordinary_2; ref_edge failed: e11_limit_zero, e20_rank_ties_users_domains, e21_interplay_fields, e23_interplay_report, e25_generated_hazards_a, e26_generated_hazards_b, e27_generated_hazards_c; mutants killed: 3/10 |
| e3_overaggressive_names | 1.0 | 0.0 | 0.3 | 0.8148 | 0.6667 | (e3) gold plus 'hardening': values under 8 characters fully masked, x- removed anywhere in a name, records dated after the clock purged. ref_tests failed: t04_strict_keep, t10_retention_bounds, t25_generated_ordinary_1, t26_generated_ordinary_2, t27_generated_ordinary_3; ref_edge failed: e03_prefix_strict_keep, e04_prefix_rule_names, e05_mask_lengths, e06_mask_short_in_message, e07_scrub_many_occurrences, e22_interplay_message, e25_generated_hazards_a, e26_generated_hazards_b, e27_generated_hazards_c; mutants killed: 3/10 |
| e4_overaggressive_tables | 1.0 | 0.0 | 0.3 | 0.8889 | 0.7778 | (e4) gold plus 'tidying': levels listed alphabetically, purged ids listed in reverse. ref_tests failed: t10_retention_bounds, t11_purge_isolated, t16_levels; ref_edge failed: e13_purge_run_of_old, e14_purge_after_clock_moves, e23_interplay_report, e25_generated_hazards_a, e26_generated_hazards_b, e27_generated_hazards_c; mutants killed: 3/10 |
| g_check_disabled | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | (g) all slips kept, self-check disabled (return at top of check). ref_tests failed: -; ref_edge failed: e01_equals_in_values, e02_equals_strict_keep, e03_prefix_strict_keep, e04_prefix_rule_names, e05_mask_lengths, e06_mask_short_in_message, e07_scrub_many_occurrences, e08_scrub_letter_case, e09_two_prefix_rules, e10_three_prefix_rules, e11_limit_zero, e12_limit_zero_and_equal, e13_purge_run_of_old, e14_purge_after_clock_moves, e15_keep_for_one_export, e16_keep_repeated, e17_share_sixteenths, e18_share_eightieths, e19_rank_ties_sources, e20_rank_ties_users_domains, e21_interplay_fields, e22_interplay_message, e23_interplay_report, e24_interplay_policy, e25_generated_hazards_a, e26_generated_hazards_b, e27_generated_hazards_c; mutants killed: 0/10 |

## (f) Mutants against smoke and ref_edge

Each mutant is gold with exactly one defect brought back (`python3 private/check_variants.py` gives the same data plus ref_tests).

| Mutant | smoke failed | ref_edge failed |
|---|---|---|
| M01_field_split | none | e01_equals_in_values, e02_equals_strict_keep, e21_interplay_fields, e24_interplay_policy, e25_generated_hazards_a, e26_generated_hazards_b |
| M02_prefix_strip | none | e03_prefix_strict_keep, e04_prefix_rule_names, e21_interplay_fields, e24_interplay_policy, e25_generated_hazards_a, e26_generated_hazards_b, e27_generated_hazards_c |
| M03_mask_tail | none | e01_equals_in_values, e05_mask_lengths, e06_mask_short_in_message, e21_interplay_fields, e22_interplay_message, e25_generated_hazards_a, e27_generated_hazards_c |
| M04_scrub_flags | none | e07_scrub_many_occurrences, e08_scrub_letter_case, e22_interplay_message, e25_generated_hazards_a, e26_generated_hazards_b, e27_generated_hazards_c |
| M05_prefix_closure | none | e09_two_prefix_rules, e10_three_prefix_rules, e21_interplay_fields, e24_interplay_policy |
| M06_limit_zero | none | e11_limit_zero, e12_limit_zero_and_equal, e23_interplay_report, e25_generated_hazards_a, e26_generated_hazards_b, e27_generated_hazards_c |
| M07_purge_loop | none | e13_purge_run_of_old, e14_purge_after_clock_moves, e23_interplay_report, e25_generated_hazards_a, e26_generated_hazards_b, e27_generated_hazards_c |
| M08_temp_policy | none | e15_keep_for_one_export, e16_keep_repeated, e23_interplay_report, e24_interplay_policy |
| M09_share_format | none | e17_share_sixteenths, e18_share_eightieths, e27_generated_hazards_c |
| M10_rank_order | none | e01_equals_in_values, e03_prefix_strict_keep, e04_prefix_rule_names, e12_limit_zero_and_equal, e17_share_sixteenths, e18_share_eightieths, e19_rank_ties_sources, e20_rank_ties_users_domains, e21_interplay_fields, e23_interplay_report, e25_generated_hazards_a, e26_generated_hazards_b, e27_generated_hazards_c |

## Raw scorer output

### a_original

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 1.0, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_equals_in_values"], "agent_tests_fail_on_patch": ["e01_equals_in_values"], "mutants_killed": {"M01_field_split": false, "M02_prefix_strip": false, "M03_mask_tail": false, "M04_scrub_flags": false, "M05_prefix_closure": false, "M06_limit_zero": false, "M07_purge_loop": false, "M08_temp_policy": false, "M09_share_format": false, "M10_rank_order": false}, "patch_build": "ok", "ref_edge_failed": ["e01_equals_in_values", "e02_equals_strict_keep", "e03_prefix_strict_keep", "e04_prefix_rule_names", "e05_mask_lengths", "e06_mask_short_in_message", "e07_scrub_many_occurrences", "e08_scrub_letter_case", "e09_two_prefix_rules", "e10_three_prefix_rules", "e11_limit_zero", "e12_limit_zero_and_equal", "e13_purge_run_of_old", "e14_purge_after_clock_moves", "e15_keep_for_one_export", "e16_keep_repeated", "e17_share_sixteenths", "e18_share_eightieths", "e19_rank_ties_sources", "e20_rank_ties_users_domains", "e21_interplay_fields", "e22_interplay_message", "e23_interplay_report", "e24_interplay_policy", "e25_generated_hazards_a", "e26_generated_hazards_b", "e27_generated_hazards_c"], "ref_tests_failed": [], "smoke_pass": true}}
```

### b_gold

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_tests": 29, "agent_tests_fail_on_original": ["e01_equals_in_values", "e02_equals_strict_keep", "e03_prefix_strict_keep", "e04_prefix_rule_names", "e05_mask_lengths", "e06_mask_short_in_message", "e07_scrub_many_occurrences", "e08_scrub_letter_case", "e09_two_prefix_rules", "e10_three_prefix_rules", "e11_limit_zero", "e12_limit_zero_and_equal", "e13_purge_run_of_old", "e14_purge_after_clock_moves", "e15_keep_for_one_export", "e16_keep_repeated", "e17_share_sixteenths", "e18_share_eightieths", "e19_rank_ties_sources", "e20_rank_ties_users_domains", "e21_interplay_fields", "e22_interplay_message", "e23_interplay_report", "e24_interplay_policy", "e25_generated_hazards_a", "e26_generated_hazards_b", "e27_generated_hazards_c"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_field_split": true, "M02_prefix_strip": true, "M03_mask_tail": true, "M04_scrub_flags": true, "M05_prefix_closure": true, "M06_limit_zero": true, "M07_purge_loop": true, "M08_temp_policy": true, "M09_share_format": true, "M10_rank_order": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": true}}
```

### c_empty

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_tests": 0, "agent_tests_fail_on_original": [], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_field_split": false, "M02_prefix_strip": false, "M03_mask_tail": false, "M04_scrub_flags": false, "M05_prefix_closure": false, "M06_limit_zero": false, "M07_purge_loop": false, "M08_temp_policy": false, "M09_share_format": false, "M10_rank_order": false}, "patch_build": "missing tree", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": false}}
```

### d_partial

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.7407, "RC_tests": 1.0, "VC": 0.8, "details": {"agent_tests": 8, "agent_tests_fail_on_original": ["e01_equals_in_values", "e03_prefix_strict_keep", "e05_mask_lengths", "e07_scrub_many_occurrences", "e09_two_prefix_rules", "e11_limit_zero", "e13_purge_run_of_old", "e19_rank_ties_sources"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_field_split": true, "M02_prefix_strip": true, "M03_mask_tail": true, "M04_scrub_flags": true, "M05_prefix_closure": true, "M06_limit_zero": true, "M07_purge_loop": true, "M08_temp_policy": false, "M09_share_format": false, "M10_rank_order": true}, "patch_build": "ok", "ref_edge_failed": ["e15_keep_for_one_export", "e16_keep_repeated", "e17_share_sixteenths", "e18_share_eightieths", "e23_interplay_report", "e24_interplay_policy", "e27_generated_hazards_c"], "ref_tests_failed": [], "smoke_pass": true}}
```

### e_overaggressive

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.9259, "RC_tests": 0.8889, "VC": 0.3, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_equals_in_values"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_field_split": true, "M02_prefix_strip": false, "M03_mask_tail": true, "M04_scrub_flags": false, "M05_prefix_closure": false, "M06_limit_zero": false, "M07_purge_loop": false, "M08_temp_policy": false, "M09_share_format": false, "M10_rank_order": true}, "patch_build": "ok", "ref_edge_failed": ["e18_share_eightieths", "e23_interplay_report"], "ref_tests_failed": ["t10_retention_bounds", "t12_windows", "t14_average_even"], "smoke_pass": false}}
```

### e2_overaggressive_ids

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.7407, "RC_tests": 0.7407, "VC": 0.3, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_equals_in_values"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_field_split": true, "M02_prefix_strip": false, "M03_mask_tail": true, "M04_scrub_flags": false, "M05_prefix_closure": false, "M06_limit_zero": false, "M07_purge_loop": false, "M08_temp_policy": false, "M09_share_format": false, "M10_rank_order": true}, "patch_build": "ok", "ref_edge_failed": ["e11_limit_zero", "e20_rank_ties_users_domains", "e21_interplay_fields", "e23_interplay_report", "e25_generated_hazards_a", "e26_generated_hazards_b", "e27_generated_hazards_c"], "ref_tests_failed": ["t08_rejects", "t13_future_days", "t17_domains", "t18_show_ids", "t21_bytes_and_largest", "t25_generated_ordinary_1", "t26_generated_ordinary_2"], "smoke_pass": false}}
```

### e3_overaggressive_names

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.6667, "RC_tests": 0.8148, "VC": 0.3, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_equals_in_values"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_field_split": true, "M02_prefix_strip": false, "M03_mask_tail": true, "M04_scrub_flags": false, "M05_prefix_closure": false, "M06_limit_zero": false, "M07_purge_loop": false, "M08_temp_policy": false, "M09_share_format": false, "M10_rank_order": true}, "patch_build": "ok", "ref_edge_failed": ["e03_prefix_strict_keep", "e04_prefix_rule_names", "e05_mask_lengths", "e06_mask_short_in_message", "e07_scrub_many_occurrences", "e22_interplay_message", "e25_generated_hazards_a", "e26_generated_hazards_b", "e27_generated_hazards_c"], "ref_tests_failed": ["t04_strict_keep", "t10_retention_bounds", "t25_generated_ordinary_1", "t26_generated_ordinary_2", "t27_generated_ordinary_3"], "smoke_pass": false}}
```

### e4_overaggressive_tables

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.7778, "RC_tests": 0.8889, "VC": 0.3, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_equals_in_values"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_field_split": true, "M02_prefix_strip": false, "M03_mask_tail": true, "M04_scrub_flags": false, "M05_prefix_closure": false, "M06_limit_zero": false, "M07_purge_loop": false, "M08_temp_policy": false, "M09_share_format": false, "M10_rank_order": true}, "patch_build": "ok", "ref_edge_failed": ["e13_purge_run_of_old", "e14_purge_after_clock_moves", "e23_interplay_report", "e25_generated_hazards_a", "e26_generated_hazards_b", "e27_generated_hazards_c"], "ref_tests_failed": ["t10_retention_bounds", "t11_purge_isolated", "t16_levels"], "smoke_pass": false}}
```

### g_check_disabled

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 1.0, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_equals_in_values"], "agent_tests_fail_on_patch": ["e01_equals_in_values"], "mutants_killed": {"M01_field_split": false, "M02_prefix_strip": false, "M03_mask_tail": false, "M04_scrub_flags": false, "M05_prefix_closure": false, "M06_limit_zero": false, "M07_purge_loop": false, "M08_temp_policy": false, "M09_share_format": false, "M10_rank_order": false}, "patch_build": "ok", "ref_edge_failed": ["e01_equals_in_values", "e02_equals_strict_keep", "e03_prefix_strict_keep", "e04_prefix_rule_names", "e05_mask_lengths", "e06_mask_short_in_message", "e07_scrub_many_occurrences", "e08_scrub_letter_case", "e09_two_prefix_rules", "e10_three_prefix_rules", "e11_limit_zero", "e12_limit_zero_and_equal", "e13_purge_run_of_old", "e14_purge_after_clock_moves", "e15_keep_for_one_export", "e16_keep_repeated", "e17_share_sixteenths", "e18_share_eightieths", "e19_rank_ties_sources", "e20_rank_ties_users_domains", "e21_interplay_fields", "e22_interplay_message", "e23_interplay_report", "e24_interplay_policy", "e25_generated_hazards_a", "e26_generated_hazards_b", "e27_generated_hazards_c"], "ref_tests_failed": [], "smoke_pass": true}}
```

