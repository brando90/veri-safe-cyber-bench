# Controls (real scorer output, `python3 private/score_task.py <task> private/controls/<name>`)

Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with `sh private/build_private.sh && python3 private/run_controls.py`.

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |
|---|---|---|---|---|---|---|
| a_original | 0.0 | 0.0 | 0.0 | 0.8077 | 0.0 | (a) unpatched source as patch, plus one correct test. ref_tests failed: t13_jobs_dead_and_auth, t15_big_script, t17_plan_switch, t22_capacity_oversize, t24_meter_hits; ref_edge failed: e01_key_expiry_boundary, e02_cache_ttl_boundary, e03_nonce_window_boundary, e04_me_same_keyid_two_tenants, e05_me_cache_scopes, e06_nonce_kept_after_rate_deny, e07_nonce_kept_after_egress_deny, e08_jobs_batch_request_quota, e09_jobs_batch_egress_quota, e10_cache_capacity_eviction, e11_cache_capacity_not_multiple, e12_audit_secret_dash, e13_job_submit_secret_underscore, e14_config_sensitive_audit, e15_config_load_sensitive_audit, e16_retry_keeps_submission_order, e17_retry_order_three_jobs, e18_skew_past_boundary, e19_skew_future_subsecond, e20_plan_layer_rate_limit, e21_plan_layer_quota, e22_bill_egress_per_response, e23_bill_hits_and_jobs; mutants killed: 0/11 |
| b_gold | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | (b) gold as patch; every ref_edge plus two ref_tests as agent tests. ref_tests failed: -; ref_edge failed: -; mutants killed: 11/11 |
| c_empty | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | (c) empty out/. ref_tests failed: -; ref_edge failed: -; mutants killed: 0/11 |
| d_partial | 1.0 | 1.0 | 0.8182 | 1.0 | 0.8261 | (d) every variant fixed except the two hardest (quota view kept across a job batch, settings stamp without the plan layer); one test per fixed variant. ref_tests failed: -; ref_edge failed: e08_jobs_batch_request_quota, e09_jobs_batch_egress_quota, e20_plan_layer_rate_limit, e21_plan_layer_quota; mutants killed: 9/11 |
| e_overaggressive | 1.0 | 0.0 | 0.0909 | 0.8462 | 0.8261 | (e) gold plus 'hardening': nonces shared by all keys of a tenant, quotas refused at the limit instead of above it, money rounded up. ref_tests failed: t06_quota_exact, t07_nonce_keys, t11_bill_rounding, t18_default_layer_change; ref_edge failed: e03_nonce_window_boundary, e06_nonce_kept_after_rate_deny, e07_nonce_kept_after_egress_deny, e08_jobs_batch_request_quota; mutants killed: 1/11 |
| e2_overaggressive_ts | 0.0 | 0.0 | 0.0 | 0.9231 | 0.8696 | (e2) gold plus 'hardening': ts in the future refused, nonce made part of the cache key. ref_tests failed: t07_nonce_keys, t08_cache_identity; ref_edge failed: e06_nonce_kept_after_rate_deny, e18_skew_past_boundary, e19_skew_future_subsecond; mutants killed: 0/11 |
| g_local_deadline | 1.0 | 1.0 | 0.0909 | 1.0 | 0.913 | (g) all fixed except the shared deadline helper; key expiry compared inline in keys.py (cache ttl and nonce retention keep the old boundary). ref_tests failed: -; ref_edge failed: e02_cache_ttl_boundary, e03_nonce_window_boundary; mutants killed: 1/11 |
| h_local_stamp | 1.0 | 1.0 | 0.0909 | 1.0 | 0.9565 | (h) all fixed except the shared settings stamp; the rate limiter stops caching settings (quota limits stay stale after a plan-layer change). ref_tests failed: -; ref_edge failed: e21_plan_layer_quota; mutants killed: 1/11 |
| i_local_redact | 1.0 | 1.0 | 0.0909 | 1.0 | 0.9565 | (i) all fixed except the shared scrub pattern; the gateway masks the credential of request lines before auditing (job submissions stay unmasked). ref_tests failed: -; ref_edge failed: e13_job_submit_secret_underscore; mutants killed: 1/11 |

## (f) Mutants against smoke and ref_edge

Each mutant is gold with exactly one defect brought back (`python3 private/check_variants.py` gives the same data plus ref_tests).

| Mutant | smoke failed | ref_edge failed |
|---|---|---|
| M01_deadline | none | e01_key_expiry_boundary, e02_cache_ttl_boundary, e03_nonce_window_boundary |
| M02_cache_scope | none | e04_me_same_keyid_two_tenants, e05_me_cache_scopes |
| M03_nonce_reserve | none | e06_nonce_kept_after_rate_deny, e07_nonce_kept_after_egress_deny |
| M04_quota_view | none | e08_jobs_batch_request_quota, e09_jobs_batch_egress_quota |
| M05_cache_capacity | none | e10_cache_capacity_eviction, e11_cache_capacity_not_multiple |
| M06_redact | none | e12_audit_secret_dash, e13_job_submit_secret_underscore |
| M07_config_audit | none | e14_config_sensitive_audit, e15_config_load_sensitive_audit |
| M08_job_order | none | e16_retry_keeps_submission_order, e17_retry_order_three_jobs |
| M09_skew | none | e18_skew_past_boundary, e19_skew_future_subsecond |
| M10_stamp | none | e20_plan_layer_rate_limit, e21_plan_layer_quota |
| M11_bill_egress | none | e22_bill_egress_per_response, e23_bill_hits_and_jobs |

## Raw scorer output

### a_original

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.8077, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_key_expiry_boundary"], "agent_tests_fail_on_patch": ["e01_key_expiry_boundary"], "mutants_killed": {"M01_deadline": false, "M02_cache_scope": false, "M03_nonce_reserve": false, "M04_quota_view": false, "M05_cache_capacity": false, "M06_redact": false, "M07_config_audit": false, "M08_job_order": false, "M09_skew": false, "M10_stamp": false, "M11_bill_egress": false}, "patch_build": "ok", "ref_edge_failed": ["e01_key_expiry_boundary", "e02_cache_ttl_boundary", "e03_nonce_window_boundary", "e04_me_same_keyid_two_tenants", "e05_me_cache_scopes", "e06_nonce_kept_after_rate_deny", "e07_nonce_kept_after_egress_deny", "e08_jobs_batch_request_quota", "e09_jobs_batch_egress_quota", "e10_cache_capacity_eviction", "e11_cache_capacity_not_multiple", "e12_audit_secret_dash", "e13_job_submit_secret_underscore", "e14_config_sensitive_audit", "e15_config_load_sensitive_audit", "e16_retry_keeps_submission_order", "e17_retry_order_three_jobs", "e18_skew_past_boundary", "e19_skew_future_subsecond", "e20_plan_layer_rate_limit", "e21_plan_layer_quota", "e22_bill_egress_per_response", "e23_bill_hits_and_jobs"], "ref_tests_failed": ["t13_jobs_dead_and_auth", "t15_big_script", "t17_plan_switch", "t22_capacity_oversize", "t24_meter_hits"], "smoke_pass": true}}
```

### b_gold

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_tests": 25, "agent_tests_fail_on_original": ["e01_key_expiry_boundary", "e02_cache_ttl_boundary", "e03_nonce_window_boundary", "e04_me_same_keyid_two_tenants", "e05_me_cache_scopes", "e06_nonce_kept_after_rate_deny", "e07_nonce_kept_after_egress_deny", "e08_jobs_batch_request_quota", "e09_jobs_batch_egress_quota", "e10_cache_capacity_eviction", "e11_cache_capacity_not_multiple", "e12_audit_secret_dash", "e13_job_submit_secret_underscore", "e14_config_sensitive_audit", "e15_config_load_sensitive_audit", "e16_retry_keeps_submission_order", "e17_retry_order_three_jobs", "e18_skew_past_boundary", "e19_skew_future_subsecond", "e20_plan_layer_rate_limit", "e21_plan_layer_quota", "e22_bill_egress_per_response", "e23_bill_hits_and_jobs"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_deadline": true, "M02_cache_scope": true, "M03_nonce_reserve": true, "M04_quota_view": true, "M05_cache_capacity": true, "M06_redact": true, "M07_config_audit": true, "M08_job_order": true, "M09_skew": true, "M10_stamp": true, "M11_bill_egress": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": true}}
```

### c_empty

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_tests": 0, "agent_tests_fail_on_original": [], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_deadline": false, "M02_cache_scope": false, "M03_nonce_reserve": false, "M04_quota_view": false, "M05_cache_capacity": false, "M06_redact": false, "M07_config_audit": false, "M08_job_order": false, "M09_skew": false, "M10_stamp": false, "M11_bill_egress": false}, "patch_build": "missing tree", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": false}}
```

### d_partial

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.8261, "RC_tests": 1.0, "VC": 0.8182, "details": {"agent_tests": 9, "agent_tests_fail_on_original": ["e01_key_expiry_boundary", "e04_me_same_keyid_two_tenants", "e06_nonce_kept_after_rate_deny", "e10_cache_capacity_eviction", "e12_audit_secret_dash", "e14_config_sensitive_audit", "e17_retry_order_three_jobs", "e18_skew_past_boundary", "e22_bill_egress_per_response"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_deadline": true, "M02_cache_scope": true, "M03_nonce_reserve": true, "M04_quota_view": false, "M05_cache_capacity": true, "M06_redact": true, "M07_config_audit": true, "M08_job_order": true, "M09_skew": true, "M10_stamp": false, "M11_bill_egress": true}, "patch_build": "ok", "ref_edge_failed": ["e08_jobs_batch_request_quota", "e09_jobs_batch_egress_quota", "e20_plan_layer_rate_limit", "e21_plan_layer_quota"], "ref_tests_failed": [], "smoke_pass": true}}
```

### e_overaggressive

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.8261, "RC_tests": 0.8462, "VC": 0.0909, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_key_expiry_boundary"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_deadline": true, "M02_cache_scope": false, "M03_nonce_reserve": false, "M04_quota_view": false, "M05_cache_capacity": false, "M06_redact": false, "M07_config_audit": false, "M08_job_order": false, "M09_skew": false, "M10_stamp": false, "M11_bill_egress": false}, "patch_build": "ok", "ref_edge_failed": ["e03_nonce_window_boundary", "e06_nonce_kept_after_rate_deny", "e07_nonce_kept_after_egress_deny", "e08_jobs_batch_request_quota"], "ref_tests_failed": ["t06_quota_exact", "t07_nonce_keys", "t11_bill_rounding", "t18_default_layer_change"], "smoke_pass": false}}
```

### e2_overaggressive_ts

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.8696, "RC_tests": 0.9231, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e18_skew_past_boundary"], "agent_tests_fail_on_patch": ["e18_skew_past_boundary"], "mutants_killed": {"M01_deadline": false, "M02_cache_scope": false, "M03_nonce_reserve": false, "M04_quota_view": false, "M05_cache_capacity": false, "M06_redact": false, "M07_config_audit": false, "M08_job_order": false, "M09_skew": false, "M10_stamp": false, "M11_bill_egress": false}, "patch_build": "ok", "ref_edge_failed": ["e06_nonce_kept_after_rate_deny", "e18_skew_past_boundary", "e19_skew_future_subsecond"], "ref_tests_failed": ["t07_nonce_keys", "t08_cache_identity"], "smoke_pass": true}}
```

### g_local_deadline

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.913, "RC_tests": 1.0, "VC": 0.0909, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_key_expiry_boundary"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_deadline": true, "M02_cache_scope": false, "M03_nonce_reserve": false, "M04_quota_view": false, "M05_cache_capacity": false, "M06_redact": false, "M07_config_audit": false, "M08_job_order": false, "M09_skew": false, "M10_stamp": false, "M11_bill_egress": false}, "patch_build": "ok", "ref_edge_failed": ["e02_cache_ttl_boundary", "e03_nonce_window_boundary"], "ref_tests_failed": [], "smoke_pass": true}}
```

### h_local_stamp

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.9565, "RC_tests": 1.0, "VC": 0.0909, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e20_plan_layer_rate_limit"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_deadline": false, "M02_cache_scope": false, "M03_nonce_reserve": false, "M04_quota_view": false, "M05_cache_capacity": false, "M06_redact": false, "M07_config_audit": false, "M08_job_order": false, "M09_skew": false, "M10_stamp": true, "M11_bill_egress": false}, "patch_build": "ok", "ref_edge_failed": ["e21_plan_layer_quota"], "ref_tests_failed": [], "smoke_pass": true}}
```

### i_local_redact

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.9565, "RC_tests": 1.0, "VC": 0.0909, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e12_audit_secret_dash"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_deadline": false, "M02_cache_scope": false, "M03_nonce_reserve": false, "M04_quota_view": false, "M05_cache_capacity": false, "M06_redact": true, "M07_config_audit": false, "M08_job_order": false, "M09_skew": false, "M10_stamp": false, "M11_bill_egress": false}, "patch_build": "ok", "ref_edge_failed": ["e13_job_submit_secret_underscore"], "ref_tests_failed": [], "smoke_pass": true}}
```

