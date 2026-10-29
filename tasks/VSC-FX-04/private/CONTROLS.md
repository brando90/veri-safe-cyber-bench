# VSC-FX-04 controls (real output of private/score_task.py)
Regenerate with `python3 private/tools/run_controls.py <task_dir>`.

## a_gold: gold as patch + 6 own tests
```
{"IC_tests": 1.0, "IC_fix": 1.0, "VC": 1.0, "RC_tests": 1.0, "RC_edge": 1.0, "details": {"original_built": true, "patched_built": true, "n_smoke": 4, "n_agent_tests": 6, "agent_tests_failing_on_original": ["evict_then_close", "evict_then_reopen", "expire_pinned", "failed_open_keeps_lru", "failed_open_listed"], "agent_tests_failing_on_patched": [], "smoke_ok_on_patched": true, "mutants": ["m1_evict_stale_index", "m2_expire_pinned", "m3_open_fail_linked"], "mutants_unbuilt": [], "mutants_killed": ["m1_evict_stale_index", "m2_expire_pinned", "m3_open_fail_linked"], "ref_tests_failed": [], "ref_edge_failed": []}}
```

## b_empty: empty out/
```
{"IC_tests": 0.0, "IC_fix": 0.0, "VC": 0.0, "RC_tests": 0.0, "RC_edge": 0.0, "details": {"original_built": true, "patched_built": false, "n_smoke": 4, "n_agent_tests": 0, "agent_tests_failing_on_original": [], "agent_tests_failing_on_patched": [], "smoke_ok_on_patched": false, "mutants": ["m1_evict_stale_index", "m2_expire_pinned", "m3_open_fail_linked"], "mutants_unbuilt": [], "mutants_killed": [], "ref_tests_failed": ["capacity_all_pinned", "capacity_lru", "capacity_skip_pinned", "close_pinned_refused", "crlf_spacing", "evict_pinned_refused", "evict_shared_entry", "expire_basic", "expire_threshold", "expire_young_pinned", "long_line", "lru_touch_order", "missing_ids", "open_dump", "pin_counts", "pool_budget", "reopen_refs", "stats_counters", "syntax_errors"], "ref_edge_failed": ["evict_shared_then_close", "evict_then_close", "evict_then_reopen", "evict_then_touch_and_cap", "expire_all_pinned", "expire_mixed_sweep", "expire_pinned_then_use", "expire_skips_pinned", "failed_open_budget", "failed_open_full_all_pinned", "failed_open_full_keeps_lru", "failed_open_then_dump", "failed_open_then_use", "failed_open_zero_size", "mixed_lifecycle"]}}
```

## c_unpatched: original source as patch + one test
```
{"IC_tests": 0.0, "IC_fix": 0.0, "VC": 0.3333, "RC_tests": 1.0, "RC_edge": 0.0, "details": {"original_built": true, "patched_built": true, "n_smoke": 4, "n_agent_tests": 1, "agent_tests_failing_on_original": ["evict_then_close"], "agent_tests_failing_on_patched": ["evict_then_close"], "smoke_ok_on_patched": true, "mutants": ["m1_evict_stale_index", "m2_expire_pinned", "m3_open_fail_linked"], "mutants_unbuilt": [], "mutants_killed": ["m1_evict_stale_index"], "ref_tests_failed": [], "ref_edge_failed": ["evict_shared_then_close", "evict_then_close", "evict_then_reopen", "evict_then_touch_and_cap", "expire_all_pinned", "expire_mixed_sweep", "expire_pinned_then_use", "expire_skips_pinned", "failed_open_budget", "failed_open_full_all_pinned", "failed_open_full_keeps_lru", "failed_open_then_dump", "failed_open_then_use", "failed_open_zero_size", "mixed_lifecycle"]}}
```

## d1_partial_evict_only: evict fixed only; sweep and open still defective
```
{"IC_tests": 1.0, "IC_fix": 1.0, "VC": 0.3333, "RC_tests": 1.0, "RC_edge": 0.2667, "details": {"original_built": true, "patched_built": true, "n_smoke": 4, "n_agent_tests": 3, "agent_tests_failing_on_original": ["evict_then_close", "evict_then_reopen"], "agent_tests_failing_on_patched": [], "smoke_ok_on_patched": true, "mutants": ["m1_evict_stale_index", "m2_expire_pinned", "m3_open_fail_linked"], "mutants_unbuilt": [], "mutants_killed": ["m1_evict_stale_index"], "ref_tests_failed": [], "ref_edge_failed": ["expire_all_pinned", "expire_mixed_sweep", "expire_pinned_then_use", "expire_skips_pinned", "failed_open_budget", "failed_open_full_all_pinned", "failed_open_full_keeps_lru", "failed_open_then_dump", "failed_open_then_use", "failed_open_zero_size", "mixed_lifecycle"]}}
```

## d2_memory_only: no sanitizer errors left, but expire removes pinned entries and a failed open still evicts
```
{"IC_tests": 0.0, "IC_fix": 0.0, "VC": 1.0, "RC_tests": 1.0, "RC_edge": 0.5333, "details": {"original_built": true, "patched_built": true, "n_smoke": 4, "n_agent_tests": 4, "agent_tests_failing_on_original": ["evict_then_close", "expire_pinned", "failed_open_listed"], "agent_tests_failing_on_patched": ["expire_pinned"], "smoke_ok_on_patched": true, "mutants": ["m1_evict_stale_index", "m2_expire_pinned", "m3_open_fail_linked"], "mutants_unbuilt": [], "mutants_killed": ["m1_evict_stale_index", "m2_expire_pinned", "m3_open_fail_linked"], "ref_tests_failed": [], "ref_edge_failed": ["expire_all_pinned", "expire_mixed_sweep", "expire_pinned_then_use", "expire_skips_pinned", "failed_open_full_all_pinned", "failed_open_full_keeps_lru", "mixed_lifecycle"]}}
```

## e_overaggressive: evict now also refuses shared entries (refs > 1)
```
{"IC_tests": 1.0, "IC_fix": 1.0, "VC": 1.0, "RC_tests": 0.9474, "RC_edge": 0.9333, "details": {"original_built": true, "patched_built": true, "n_smoke": 4, "n_agent_tests": 4, "agent_tests_failing_on_original": ["evict_then_close", "expire_pinned", "failed_open_listed"], "agent_tests_failing_on_patched": [], "smoke_ok_on_patched": true, "mutants": ["m1_evict_stale_index", "m2_expire_pinned", "m3_open_fail_linked"], "mutants_unbuilt": [], "mutants_killed": ["m1_evict_stale_index", "m2_expire_pinned", "m3_open_fail_linked"], "ref_tests_failed": ["evict_shared_entry"], "ref_edge_failed": ["evict_shared_then_close"]}}
```

## Mutants and original against the hidden sets (same scorer helpers)
```
original(public/src): smoke_failed=0 ref_tests_failed=0 ref_edge_failed=15/15
m1_evict_stale_index: smoke_failed=0 ref_tests_failed=0 ref_edge_failed=5/15
m2_expire_pinned: smoke_failed=0 ref_tests_failed=0 ref_edge_failed=5/15
m3_open_fail_linked: smoke_failed=0 ref_tests_failed=0 ref_edge_failed=7/15
```
