# Controls (real scorer output, `python3 private/score_task.py <task> private/controls/<name>`)

Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with `sh private/build_private.sh && python3 private/run_controls.py`.

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |
|---|---|---|---|---|---|---|
| a_original | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | (a) unpatched source as patch, plus one correct test. ref_tests failed: -; ref_edge failed: e01_sms_partial_block, e02_sms_invoice, e03_queue_tier_boundary, e04_queue_invoice, e05_es_exempt_invoice, e06_es_exempt_toggle, e07_fr_tax_half, e08_fr_tax_discount_late, e09_fixed_fee_cap, e10_fixed_kinds_caps, e11_chf_half_quote, e12_chf_invoice, e13_phone_closed, e14_phone_closed_audit, e15_dun_due_day, e16_dun_day_after, e17_plan_change_mid, e18_plan_change_edges, e19_refund_twice, e20_refund_boundary, e21_tax_report_after_void, e22_tax_report_filters, e23_batch_same_prefix, e24_batch_vs_single, e25_sweep_quotes, e26_sweep_regions, e27_sweep_currencies; mutants killed: 0/12 |
| b_gold | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | (b) gold as patch; every ref_edge plus two ref_tests as agent tests. ref_tests failed: -; ref_edge failed: -; mutants killed: 12/12 |
| c_empty | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | (c) empty out/. ref_tests failed: -; ref_edge failed: -; mutants killed: 0/12 |
| d_partial | 1.0 | 1.0 | 0.8333 | 1.0 | 0.7778 | (d) every variant fixed except the two quietest (the fixed_fee coupon cap and the CHF conversion rounding); one test per fixed variant. ref_tests failed: -; ref_edge failed: e09_fixed_fee_cap, e10_fixed_kinds_caps, e11_chf_half_quote, e12_chf_invoice, e25_sweep_quotes, e27_sweep_currencies; mutants killed: 10/12 |
| e_overaggressive | 1.0 | 1.0 | 0.0833 | 0.8462 | 0.8889 | (e) gold plus 'hardening' of deliberate exceptions: whole-block services rounded up, split-rate regions taxed at one rate, the voided report limited to live invoices. ref_tests failed: t03_usage_rating_basic, t04_whole_mode_services, t15_void_rules, t26_big_script; ref_edge failed: e22_tax_report_filters, e25_sweep_quotes, e26_sweep_regions; mutants killed: 1/12 |
| e2_overaggressive_closed | 1.0 | 0.0 | 0.0833 | 0.8077 | 0.9259 | (e2) gold plus 'hardening': refunds and statements refused for closed customers, and late fees taxed. ref_tests failed: t14_refund_basic, t16_dunning_basic, t18_reports_grouped, t20_closed_customer, t26_big_script; ref_edge failed: e15_dun_due_day, e16_dun_day_after; mutants killed: 1/12 |
| g_minority_overdue | 1.0 | 1.0 | 0.0833 | 1.0 | 0.9259 | (g) all fixed except the overdue boundary, harmonised the wrong way: the shared timeutil.is_overdue changed to '>=' so dun charges on the due day. ref_tests failed: -; ref_edge failed: e15_dun_due_day, e16_dun_day_after; mutants killed: 1/12 |
| h_minority_pct | 1.0 | 0.0 | 0.0833 | 0.1923 | 0.3333 | (h) all fixed except the tax rounding, harmonised the wrong way: the shared money.pct changed to truncate. ref_tests failed: t02_first_invoice_proration, t04_whole_mode_services, t05_tier_boundaries, t06_coupon_kinds, t07_coupon_until_n, t08_tax_regions, t10_currencies, t11_payment_order, t12_pay_direct_overpay, t13_credit_flow, t14_refund_basic, t15_void_rules, t16_dunning_basic, t17_aging_buckets, t18_reports_grouped, t19_top_ranking, t20_closed_customer, t21_usage_validation, t22_batch_single_customer, t24_audit_ledger_statement, t26_big_script; ref_edge failed: e02_sms_invoice, e04_queue_invoice, e06_es_exempt_toggle, e07_fr_tax_half, e08_fr_tax_discount_late, e09_fixed_fee_cap, e10_fixed_kinds_caps, e12_chf_invoice, e15_dun_due_day, e16_dun_day_after, e17_plan_change_mid, e18_plan_change_edges, e19_refund_twice, e20_refund_boundary, e21_tax_report_after_void, e22_tax_report_filters, e26_sweep_regions, e27_sweep_currencies; mutants killed: 1/12 |

## (f) Mutants against smoke and ref_edge

Each mutant is gold with exactly one defect brought back (`python3 private/check_variants.py` gives the same data plus ref_tests).

| Mutant | smoke failed | ref_edge failed |
|---|---|---|
| M01_sms_blocks | none | e01_sms_partial_block, e02_sms_invoice, e25_sweep_quotes |
| M02_queue_tier | none | e03_queue_tier_boundary, e04_queue_invoice, e25_sweep_quotes |
| M03_es_exempt | none | e05_es_exempt_invoice, e06_es_exempt_toggle, e26_sweep_regions |
| M04_fr_rounding | none | e07_fr_tax_half, e08_fr_tax_discount_late, e26_sweep_regions |
| M05_fixed_fee_cap | none | e09_fixed_fee_cap, e10_fixed_kinds_caps |
| M06_chf_rounding | none | e11_chf_half_quote, e12_chf_invoice, e25_sweep_quotes, e27_sweep_currencies |
| M07_phone_closed | none | e13_phone_closed, e14_phone_closed_audit |
| M08_dun_boundary | none | e15_dun_due_day, e16_dun_day_after |
| M09_plan_days | none | e17_plan_change_mid, e18_plan_change_edges |
| M10_refund_cap | none | e19_refund_twice, e20_refund_boundary |
| M11_tax_report_void | none | e21_tax_report_after_void, e22_tax_report_filters |
| M12_batch_key | none | e23_batch_same_prefix, e24_batch_vs_single |

## Raw scorer output

### a_original

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 1.0, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_sms_partial_block"], "agent_tests_fail_on_patch": ["e01_sms_partial_block"], "mutants_killed": {"M01_sms_blocks": false, "M02_queue_tier": false, "M03_es_exempt": false, "M04_fr_rounding": false, "M05_fixed_fee_cap": false, "M06_chf_rounding": false, "M07_phone_closed": false, "M08_dun_boundary": false, "M09_plan_days": false, "M10_refund_cap": false, "M11_tax_report_void": false, "M12_batch_key": false}, "patch_build": "ok", "ref_edge_failed": ["e01_sms_partial_block", "e02_sms_invoice", "e03_queue_tier_boundary", "e04_queue_invoice", "e05_es_exempt_invoice", "e06_es_exempt_toggle", "e07_fr_tax_half", "e08_fr_tax_discount_late", "e09_fixed_fee_cap", "e10_fixed_kinds_caps", "e11_chf_half_quote", "e12_chf_invoice", "e13_phone_closed", "e14_phone_closed_audit", "e15_dun_due_day", "e16_dun_day_after", "e17_plan_change_mid", "e18_plan_change_edges", "e19_refund_twice", "e20_refund_boundary", "e21_tax_report_after_void", "e22_tax_report_filters", "e23_batch_same_prefix", "e24_batch_vs_single", "e25_sweep_quotes", "e26_sweep_regions", "e27_sweep_currencies"], "ref_tests_failed": [], "smoke_pass": true}}
```

### b_gold

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_tests": 29, "agent_tests_fail_on_original": ["e01_sms_partial_block", "e02_sms_invoice", "e03_queue_tier_boundary", "e04_queue_invoice", "e05_es_exempt_invoice", "e06_es_exempt_toggle", "e07_fr_tax_half", "e08_fr_tax_discount_late", "e09_fixed_fee_cap", "e10_fixed_kinds_caps", "e11_chf_half_quote", "e12_chf_invoice", "e13_phone_closed", "e14_phone_closed_audit", "e15_dun_due_day", "e16_dun_day_after", "e17_plan_change_mid", "e18_plan_change_edges", "e19_refund_twice", "e20_refund_boundary", "e21_tax_report_after_void", "e22_tax_report_filters", "e23_batch_same_prefix", "e24_batch_vs_single", "e25_sweep_quotes", "e26_sweep_regions", "e27_sweep_currencies"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_sms_blocks": true, "M02_queue_tier": true, "M03_es_exempt": true, "M04_fr_rounding": true, "M05_fixed_fee_cap": true, "M06_chf_rounding": true, "M07_phone_closed": true, "M08_dun_boundary": true, "M09_plan_days": true, "M10_refund_cap": true, "M11_tax_report_void": true, "M12_batch_key": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": true}}
```

### c_empty

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_tests": 0, "agent_tests_fail_on_original": [], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_sms_blocks": false, "M02_queue_tier": false, "M03_es_exempt": false, "M04_fr_rounding": false, "M05_fixed_fee_cap": false, "M06_chf_rounding": false, "M07_phone_closed": false, "M08_dun_boundary": false, "M09_plan_days": false, "M10_refund_cap": false, "M11_tax_report_void": false, "M12_batch_key": false}, "patch_build": "missing tree", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": false}}
```

### d_partial

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.7778, "RC_tests": 1.0, "VC": 0.8333, "details": {"agent_tests": 10, "agent_tests_fail_on_original": ["e01_sms_partial_block", "e03_queue_tier_boundary", "e05_es_exempt_invoice", "e07_fr_tax_half", "e13_phone_closed", "e15_dun_due_day", "e17_plan_change_mid", "e19_refund_twice", "e21_tax_report_after_void", "e23_batch_same_prefix"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_sms_blocks": true, "M02_queue_tier": true, "M03_es_exempt": true, "M04_fr_rounding": true, "M05_fixed_fee_cap": false, "M06_chf_rounding": false, "M07_phone_closed": true, "M08_dun_boundary": true, "M09_plan_days": true, "M10_refund_cap": true, "M11_tax_report_void": true, "M12_batch_key": true}, "patch_build": "ok", "ref_edge_failed": ["e09_fixed_fee_cap", "e10_fixed_kinds_caps", "e11_chf_half_quote", "e12_chf_invoice", "e25_sweep_quotes", "e27_sweep_currencies"], "ref_tests_failed": [], "smoke_pass": true}}
```

### e_overaggressive

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.8889, "RC_tests": 0.8462, "VC": 0.0833, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_sms_partial_block"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_sms_blocks": true, "M02_queue_tier": false, "M03_es_exempt": false, "M04_fr_rounding": false, "M05_fixed_fee_cap": false, "M06_chf_rounding": false, "M07_phone_closed": false, "M08_dun_boundary": false, "M09_plan_days": false, "M10_refund_cap": false, "M11_tax_report_void": false, "M12_batch_key": false}, "patch_build": "ok", "ref_edge_failed": ["e22_tax_report_filters", "e25_sweep_quotes", "e26_sweep_regions"], "ref_tests_failed": ["t03_usage_rating_basic", "t04_whole_mode_services", "t15_void_rules", "t26_big_script"], "smoke_pass": true}}
```

### e2_overaggressive_closed

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.9259, "RC_tests": 0.8077, "VC": 0.0833, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_sms_partial_block"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_sms_blocks": true, "M02_queue_tier": false, "M03_es_exempt": false, "M04_fr_rounding": false, "M05_fixed_fee_cap": false, "M06_chf_rounding": false, "M07_phone_closed": false, "M08_dun_boundary": false, "M09_plan_days": false, "M10_refund_cap": false, "M11_tax_report_void": false, "M12_batch_key": false}, "patch_build": "ok", "ref_edge_failed": ["e15_dun_due_day", "e16_dun_day_after"], "ref_tests_failed": ["t14_refund_basic", "t16_dunning_basic", "t18_reports_grouped", "t20_closed_customer", "t26_big_script"], "smoke_pass": false}}
```

### g_minority_overdue

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.9259, "RC_tests": 1.0, "VC": 0.0833, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_sms_partial_block"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_sms_blocks": true, "M02_queue_tier": false, "M03_es_exempt": false, "M04_fr_rounding": false, "M05_fixed_fee_cap": false, "M06_chf_rounding": false, "M07_phone_closed": false, "M08_dun_boundary": false, "M09_plan_days": false, "M10_refund_cap": false, "M11_tax_report_void": false, "M12_batch_key": false}, "patch_build": "ok", "ref_edge_failed": ["e15_dun_due_day", "e16_dun_day_after"], "ref_tests_failed": [], "smoke_pass": true}}
```

### h_minority_pct

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.3333, "RC_tests": 0.1923, "VC": 0.0833, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_sms_partial_block"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_sms_blocks": true, "M02_queue_tier": false, "M03_es_exempt": false, "M04_fr_rounding": false, "M05_fixed_fee_cap": false, "M06_chf_rounding": false, "M07_phone_closed": false, "M08_dun_boundary": false, "M09_plan_days": false, "M10_refund_cap": false, "M11_tax_report_void": false, "M12_batch_key": false}, "patch_build": "ok", "ref_edge_failed": ["e02_sms_invoice", "e04_queue_invoice", "e06_es_exempt_toggle", "e07_fr_tax_half", "e08_fr_tax_discount_late", "e09_fixed_fee_cap", "e10_fixed_kinds_caps", "e12_chf_invoice", "e15_dun_due_day", "e16_dun_day_after", "e17_plan_change_mid", "e18_plan_change_edges", "e19_refund_twice", "e20_refund_boundary", "e21_tax_report_after_void", "e22_tax_report_filters", "e26_sweep_regions", "e27_sweep_currencies"], "ref_tests_failed": ["t02_first_invoice_proration", "t04_whole_mode_services", "t05_tier_boundaries", "t06_coupon_kinds", "t07_coupon_until_n", "t08_tax_regions", "t10_currencies", "t11_payment_order", "t12_pay_direct_overpay", "t13_credit_flow", "t14_refund_basic", "t15_void_rules", "t16_dunning_basic", "t17_aging_buckets", "t18_reports_grouped", "t19_top_ranking", "t20_closed_customer", "t21_usage_validation", "t22_batch_single_customer", "t24_audit_ledger_statement", "t26_big_script"], "smoke_pass": false}}
```

