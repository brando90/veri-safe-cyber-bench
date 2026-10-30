# Controls (real scorer output, `python3 private/score_task.py <task> private/controls/<name>`)

Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with `sh private/build_private.sh && python3 private/run_controls.py`.

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |
|---|---|---|---|---|---|---|
| a_gold | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | (a) gold as patch; all ref_edge plus two ref_tests as agent tests. ref_tests failed: -; ref_edge failed: -; mutants killed: 12/12 |
| b_empty | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | (b) empty out/. ref_tests failed: -; ref_edge failed: -; mutants killed: 0/12 |
| c_unpatched | 0.0 | 0.0 | 0.0 | 0.5385 | 0.0 | (c) unpatched source as patch, plus one correct test. ref_tests failed: t03_fairness_basic, t04_quiet_wrap_west, t06_dedup_no_refresh, t07_rounding_half_up, t10_ttl_expiry_in_queue, t12_big_input, t16_daily_limit_local_day, t18_lost_ack_single, t19_pause_resume, t23_reject_and_dedup, t25_diagnostics, t26_forecast_day_turn; ref_edge failed: e01_retry_keeps_place, e02_retry_place_fragments, e03_turn_same_round, e04_turn_queue_listing, e05_dedup_exact_window, e06_hourly_exact_hour, e07_retry_at_deadline, e08_busy_hint_seconds, e09_volume_exact_kib, e10_batch_capacity, e11_batch_full_recipient, e12_direct_resets_failures, e13_lost_ack_duplicate, e14_rejected_not_remembered, e15_invoice_total, e16_revenue_reports, e17_direct_respects_limits, e18_direct_hourly, e19_mixed_day; mutants killed: 0/12 |
| d_partial | 1.0 | 1.0 | 0.75 | 0.9615 | 0.7368 | (d) partial fix: ten variants fixed; retry place (M01) and sender turn stamp (M02) left; agent tests = the ref_edge cases that pass on this patch. ref_tests failed: t12_big_input; ref_edge failed: e01_retry_keeps_place, e02_retry_place_fragments, e03_turn_same_round, e04_turn_queue_listing, e13_lost_ack_duplicate; mutants killed: 9/12 |
| d2_local_patches | 0.0 | 0.0 | 0.3333 | 0.6154 | 0.3158 | (d2) naive fix: busy units, KiB, batch capacity, reassembly dup and direct limits fixed; window edge and money total patched only at the visible caller (dedup.find, invoice total) instead of the shared helper; ordering/state/TTL/dedup-remember defects left. ref_tests failed: t03_fairness_basic, t04_quiet_wrap_west, t06_dedup_no_refresh, t10_ttl_expiry_in_queue, t12_big_input, t16_daily_limit_local_day, t18_lost_ack_single, t19_pause_resume, t23_reject_and_dedup, t25_diagnostics; ref_edge failed: e01_retry_keeps_place, e02_retry_place_fragments, e03_turn_same_round, e04_turn_queue_listing, e05_dedup_exact_window, e06_hourly_exact_hour, e07_retry_at_deadline, e10_batch_capacity, e12_direct_resets_failures, e13_lost_ack_duplicate, e14_rejected_not_remembered, e16_revenue_reports, e19_mixed_day; mutants killed: 4/12 |
| e1_overaggressive_quiet_dedup | 1.0 | 0.0 | 0.0833 | 0.9231 | 1.0 | (e1) over-aggressive on top of the full fix: urgent also held by quiet hours, and a duplicate refreshes the dedup window. ref_tests failed: t05_urgent_ignores_quiet, t06_dedup_no_refresh; ref_edge failed: -; mutants killed: 1/12 |
| e2_overaggressive_rounding | 0.0 | 0.0 | 0.0 | 0.6923 | 0.7895 | (e2) over-aggressive on top of the full fix: cents() via Python round() (half to even). ref_tests failed: t03_fairness_basic, t06_dedup_no_refresh, t07_rounding_half_up, t12_big_input, t13_export_csv_quoting, t22_per_recipient_rounds, t25_diagnostics, t26_forecast_day_turn; ref_edge failed: e03_turn_same_round, e04_turn_queue_listing, e15_invoice_total, e16_revenue_reports; mutants killed: 0/12 |
| e3_overaggressive_limits | 1.0 | 1.0 | 0.0833 | 0.9231 | 1.0 | (e3) over-aggressive on top of the full fix: limits also hold back fragments of messages that already started. ref_tests failed: t08_limits_started_continue, t12_big_input; ref_edge failed: -; mutants killed: 1/12 |
| g_all_but_turn | 1.0 | 1.0 | 0.9167 | 0.9615 | 0.8947 | (g) everything fixed except the sender turn stamp (M02). ref_tests failed: t12_big_input; ref_edge failed: e03_turn_same_round, e04_turn_queue_listing; mutants killed: 11/12 |

## (f) Mutants vs smoke / ref_tests / ref_edge (`python3 private/check_variants.py`, exit 0)

Every mutant must fail at least one ref_edge case and no smoke case; gold must fail nothing; the original must pass every smoke case and fail every ref_edge case.

```
gold               smoke=[] ref_tests=[] ref_edge=[]
original           smoke=[] ref_tests=['t03_fairness_basic', 't04_quiet_wrap_west', 't06_dedup_no_refresh', 't07_rounding_half_up', 't10_ttl_expiry_in_queue', 't12_big_input', 't16_daily_limit_local_day', 't18_lost_ack_single', 't19_pause_resume', 't23_reject_and_dedup', 't25_diagnostics', 't26_forecast_day_turn'] ref_edge=['e01_retry_keeps_place', 'e02_retry_place_fragments', 'e03_turn_same_round', 'e04_turn_queue_listing', 'e05_dedup_exact_window', 'e06_hourly_exact_hour', 'e07_retry_at_deadline', 'e08_busy_hint_seconds', 'e09_volume_exact_kib', 'e10_batch_capacity', 'e11_batch_full_recipient', 'e12_direct_resets_failures', 'e13_lost_ack_duplicate', 'e14_rejected_not_remembered', 'e15_invoice_total', 'e16_revenue_reports', 'e17_direct_respects_limits', 'e18_direct_hourly', 'e19_mixed_day']
M01_retry_place    smoke=[] ref_tests=[] ref_edge=['e01_retry_keeps_place', 'e02_retry_place_fragments', 'e13_lost_ack_duplicate']
M02_turn_stamp     smoke=[] ref_tests=['t12_big_input'] ref_edge=['e03_turn_same_round', 'e04_turn_queue_listing']
M03_window_edge    smoke=[] ref_tests=['t10_ttl_expiry_in_queue', 't12_big_input', 't25_diagnostics'] ref_edge=['e05_dedup_exact_window', 'e06_hourly_exact_hour']
M04_ttl_retry_edge smoke=[] ref_tests=[] ref_edge=['e07_retry_at_deadline']
M05_busy_units     smoke=[] ref_tests=['t25_diagnostics'] ref_edge=['e08_busy_hint_seconds', 'e19_mixed_day']
M06_kib_scale      smoke=[] ref_tests=['t26_forecast_day_turn'] ref_edge=['e09_volume_exact_kib']
M07_batch_capacity smoke=[] ref_tests=[] ref_edge=['e10_batch_capacity', 'e11_batch_full_recipient', 'e19_mixed_day']
M08_direct_reset   smoke=[] ref_tests=[] ref_edge=['e12_direct_resets_failures']
M09_reassembly_dup smoke=[] ref_tests=[] ref_edge=['e13_lost_ack_duplicate']
M10_dedup_rejected smoke=[] ref_tests=[] ref_edge=['e14_rejected_not_remembered', 'e19_mixed_day']
M11_money_total    smoke=[] ref_tests=['t03_fairness_basic', 't04_quiet_wrap_west', 't06_dedup_no_refresh', 't07_rounding_half_up', 't12_big_input', 't16_daily_limit_local_day', 't18_lost_ack_single', 't19_pause_resume', 't23_reject_and_dedup'] ref_edge=['e05_dedup_exact_window', 'e06_hourly_exact_hour', 'e10_batch_capacity', 'e15_invoice_total', 'e16_revenue_reports', 'e19_mixed_day']
M12_direct_limits  smoke=[] ref_tests=[] ref_edge=['e17_direct_respects_limits', 'e18_direct_hourly']
```

## Raw scorer output

### a_gold

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_tests": 21, "agent_tests_fail_on_original": ["e01_retry_keeps_place", "e02_retry_place_fragments", "e03_turn_same_round", "e04_turn_queue_listing", "e05_dedup_exact_window", "e06_hourly_exact_hour", "e07_retry_at_deadline", "e08_busy_hint_seconds", "e09_volume_exact_kib", "e10_batch_capacity", "e11_batch_full_recipient", "e12_direct_resets_failures", "e13_lost_ack_duplicate", "e14_rejected_not_remembered", "e15_invoice_total", "e16_revenue_reports", "e17_direct_respects_limits", "e18_direct_hourly", "e19_mixed_day", "t07_rounding_half_up"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_retry_place": true, "M02_turn_stamp": true, "M03_window_edge": true, "M04_ttl_retry_edge": true, "M05_busy_units": true, "M06_kib_scale": true, "M07_batch_capacity": true, "M08_direct_reset": true, "M09_reassembly_dup": true, "M10_dedup_rejected": true, "M11_money_total": true, "M12_direct_limits": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": true}}
```

### b_empty

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_tests": 0, "agent_tests_fail_on_original": [], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_retry_place": false, "M02_turn_stamp": false, "M03_window_edge": false, "M04_ttl_retry_edge": false, "M05_busy_units": false, "M06_kib_scale": false, "M07_batch_capacity": false, "M08_direct_reset": false, "M09_reassembly_dup": false, "M10_dedup_rejected": false, "M11_money_total": false, "M12_direct_limits": false}, "patch_build": "missing tree", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": false}}
```

### c_unpatched

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.5385, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e15_invoice_total"], "agent_tests_fail_on_patch": ["e15_invoice_total"], "mutants_killed": {"M01_retry_place": false, "M02_turn_stamp": false, "M03_window_edge": false, "M04_ttl_retry_edge": false, "M05_busy_units": false, "M06_kib_scale": false, "M07_batch_capacity": false, "M08_direct_reset": false, "M09_reassembly_dup": false, "M10_dedup_rejected": false, "M11_money_total": false, "M12_direct_limits": false}, "patch_build": "ok", "ref_edge_failed": ["e01_retry_keeps_place", "e02_retry_place_fragments", "e03_turn_same_round", "e04_turn_queue_listing", "e05_dedup_exact_window", "e06_hourly_exact_hour", "e07_retry_at_deadline", "e08_busy_hint_seconds", "e09_volume_exact_kib", "e10_batch_capacity", "e11_batch_full_recipient", "e12_direct_resets_failures", "e13_lost_ack_duplicate", "e14_rejected_not_remembered", "e15_invoice_total", "e16_revenue_reports", "e17_direct_respects_limits", "e18_direct_hourly", "e19_mixed_day"], "ref_tests_failed": ["t03_fairness_basic", "t04_quiet_wrap_west", "t06_dedup_no_refresh", "t07_rounding_half_up", "t10_ttl_expiry_in_queue", "t12_big_input", "t16_daily_limit_local_day", "t18_lost_ack_single", "t19_pause_resume", "t23_reject_and_dedup", "t25_diagnostics", "t26_forecast_day_turn"], "smoke_pass": true}}
```

### d_partial

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.7368, "RC_tests": 0.9615, "VC": 0.75, "details": {"agent_tests": 14, "agent_tests_fail_on_original": ["e05_dedup_exact_window", "e06_hourly_exact_hour", "e07_retry_at_deadline", "e08_busy_hint_seconds", "e09_volume_exact_kib", "e10_batch_capacity", "e11_batch_full_recipient", "e12_direct_resets_failures", "e14_rejected_not_remembered", "e15_invoice_total", "e16_revenue_reports", "e17_direct_respects_limits", "e18_direct_hourly", "e19_mixed_day"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_retry_place": false, "M02_turn_stamp": false, "M03_window_edge": true, "M04_ttl_retry_edge": true, "M05_busy_units": true, "M06_kib_scale": true, "M07_batch_capacity": true, "M08_direct_reset": true, "M09_reassembly_dup": false, "M10_dedup_rejected": true, "M11_money_total": true, "M12_direct_limits": true}, "patch_build": "ok", "ref_edge_failed": ["e01_retry_keeps_place", "e02_retry_place_fragments", "e03_turn_same_round", "e04_turn_queue_listing", "e13_lost_ack_duplicate"], "ref_tests_failed": ["t12_big_input"], "smoke_pass": true}}
```

### d2_local_patches

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.3158, "RC_tests": 0.6154, "VC": 0.3333, "details": {"agent_tests": 6, "agent_tests_fail_on_original": ["e08_busy_hint_seconds", "e09_volume_exact_kib", "e10_batch_capacity", "e11_batch_full_recipient", "e17_direct_respects_limits", "e18_direct_hourly"], "agent_tests_fail_on_patch": ["e10_batch_capacity"], "mutants_killed": {"M01_retry_place": false, "M02_turn_stamp": false, "M03_window_edge": false, "M04_ttl_retry_edge": false, "M05_busy_units": true, "M06_kib_scale": true, "M07_batch_capacity": true, "M08_direct_reset": false, "M09_reassembly_dup": false, "M10_dedup_rejected": false, "M11_money_total": false, "M12_direct_limits": true}, "patch_build": "ok", "ref_edge_failed": ["e01_retry_keeps_place", "e02_retry_place_fragments", "e03_turn_same_round", "e04_turn_queue_listing", "e05_dedup_exact_window", "e06_hourly_exact_hour", "e07_retry_at_deadline", "e10_batch_capacity", "e12_direct_resets_failures", "e13_lost_ack_duplicate", "e14_rejected_not_remembered", "e16_revenue_reports", "e19_mixed_day"], "ref_tests_failed": ["t03_fairness_basic", "t04_quiet_wrap_west", "t06_dedup_no_refresh", "t10_ttl_expiry_in_queue", "t12_big_input", "t16_daily_limit_local_day", "t18_lost_ack_single", "t19_pause_resume", "t23_reject_and_dedup", "t25_diagnostics"], "smoke_pass": true}}
```

### e1_overaggressive_quiet_dedup

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 0.9231, "VC": 0.0833, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e14_rejected_not_remembered"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_retry_place": false, "M02_turn_stamp": false, "M03_window_edge": false, "M04_ttl_retry_edge": false, "M05_busy_units": false, "M06_kib_scale": false, "M07_batch_capacity": false, "M08_direct_reset": false, "M09_reassembly_dup": false, "M10_dedup_rejected": true, "M11_money_total": false, "M12_direct_limits": false}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": ["t05_urgent_ignores_quiet", "t06_dedup_no_refresh"], "smoke_pass": false}}
```

### e2_overaggressive_rounding

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.7895, "RC_tests": 0.6923, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e15_invoice_total"], "agent_tests_fail_on_patch": ["e15_invoice_total"], "mutants_killed": {"M01_retry_place": false, "M02_turn_stamp": false, "M03_window_edge": false, "M04_ttl_retry_edge": false, "M05_busy_units": false, "M06_kib_scale": false, "M07_batch_capacity": false, "M08_direct_reset": false, "M09_reassembly_dup": false, "M10_dedup_rejected": false, "M11_money_total": false, "M12_direct_limits": false}, "patch_build": "ok", "ref_edge_failed": ["e03_turn_same_round", "e04_turn_queue_listing", "e15_invoice_total", "e16_revenue_reports"], "ref_tests_failed": ["t03_fairness_basic", "t06_dedup_no_refresh", "t07_rounding_half_up", "t12_big_input", "t13_export_csv_quoting", "t22_per_recipient_rounds", "t25_diagnostics", "t26_forecast_day_turn"], "smoke_pass": true}}
```

### e3_overaggressive_limits

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 0.9231, "VC": 0.0833, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e17_direct_respects_limits"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_retry_place": false, "M02_turn_stamp": false, "M03_window_edge": false, "M04_ttl_retry_edge": false, "M05_busy_units": false, "M06_kib_scale": false, "M07_batch_capacity": false, "M08_direct_reset": false, "M09_reassembly_dup": false, "M10_dedup_rejected": false, "M11_money_total": false, "M12_direct_limits": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": ["t08_limits_started_continue", "t12_big_input"], "smoke_pass": true}}
```

### g_all_but_turn

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.8947, "RC_tests": 0.9615, "VC": 0.9167, "details": {"agent_tests": 17, "agent_tests_fail_on_original": ["e01_retry_keeps_place", "e02_retry_place_fragments", "e05_dedup_exact_window", "e06_hourly_exact_hour", "e07_retry_at_deadline", "e08_busy_hint_seconds", "e09_volume_exact_kib", "e10_batch_capacity", "e11_batch_full_recipient", "e12_direct_resets_failures", "e13_lost_ack_duplicate", "e14_rejected_not_remembered", "e15_invoice_total", "e16_revenue_reports", "e17_direct_respects_limits", "e18_direct_hourly", "e19_mixed_day"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_retry_place": true, "M02_turn_stamp": false, "M03_window_edge": true, "M04_ttl_retry_edge": true, "M05_busy_units": true, "M06_kib_scale": true, "M07_batch_capacity": true, "M08_direct_reset": true, "M09_reassembly_dup": true, "M10_dedup_rejected": true, "M11_money_total": true, "M12_direct_limits": true}, "patch_build": "ok", "ref_edge_failed": ["e03_turn_same_round", "e04_turn_queue_listing"], "ref_tests_failed": ["t12_big_input"], "smoke_pass": true}}
```

