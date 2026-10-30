# Controls (real scorer output, `python3 private/score_task.py <task> private/controls/<name>`)

Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with `sh private/build_private.sh && python3 private/run_controls.py`.
Letters (a)-(f) refer to the v3 control list in SPEC_TASKS.md.

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |
|---|---|---|---|---|---|---|
| a_gold | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | (b) gold as patch; all ref_edge plus two ref_tests as agent tests. ref_tests failed: -; ref_edge failed: -; mutants killed: 12/12 |
| b_empty | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | (c) empty out/. ref_tests failed: -; ref_edge failed: -; mutants killed: 0/12 |
| c_unpatched | 0.0 | 0.0 | 0.0 | 0.8077 | 0.0 | (a) unpatched original as patch, plus one correct test (RC_edge of the original). ref_tests failed: t06_named_conditions, t07_budget_exact, t08_approval_lifecycle, t16_retention_stats, t23_big_input; ref_edge failed: e01_list_nesting_limit, e02_mixed_nesting_in_rule, e03_named_condition_budget_check, e04_named_condition_budget_eval, e05_extend_after_deadline, e06_extend_pending_after_deadline, e07_use_at_deadline, e08_grant_at_deadline, e09_extend_at_deadline, e10_report_pct_half_up, e11_report_json_pct, e12_approval_single_segment, e13_rule_prefix_segment, e14_filter_and_glob_prefix, e15_approval_prefix_segment, e16_log_order_same_time, e17_report_order_same_time, e18_note_redaction, e19_html_redaction_order, e20_bundle_header_not_applied, e21_template_html_context; mutants killed: 0/12 |
| d_partial_all_but_two | 1.0 | 1.0 | 0.75 | 0.9615 | 0.8095 | (d) everything fixed except the two hardest variants (log merge order M08, html context escaping layer M12); tests = the ref_edge cases that do not need them. ref_tests failed: t16_retention_stats; ref_edge failed: e16_log_order_same_time, e17_report_order_same_time, e19_html_redaction_order, e21_template_html_context; mutants killed: 9/12 |
| d2_partial_visible | 1.0 | 1.0 | 0.3333 | 0.8077 | 0.381 | (d2) only the visible symptoms fixed (exit 86 / obvious error lines: M01, M03, M04, M09, M10); M02, M05, M06, M07, M08, M11, M12 left. ref_tests failed: t06_named_conditions, t07_budget_exact, t08_approval_lifecycle, t16_retention_stats, t23_big_input; ref_edge failed: e03_named_condition_budget_check, e04_named_condition_budget_eval, e10_report_pct_half_up, e11_report_json_pct, e12_approval_single_segment, e13_rule_prefix_segment, e14_filter_and_glob_prefix, e15_approval_prefix_segment, e16_log_order_same_time, e17_report_order_same_time, e19_html_redaction_order, e20_bundle_header_not_applied, e21_template_html_context; mutants killed: 4/12 |
| g1_local_pattern_patch | 1.0 | 1.0 | 0.0833 | 1.0 | 0.9048 | (g1) local patch: rule matching in decide.py gets its own correct /** check; the shared patterns.match_resource helper stays wrong (log filter, glob(), approvals). ref_tests failed: -; ref_edge failed: e14_filter_and_glob_prefix, e15_approval_prefix_segment; mutants killed: 1/12 |
| g2_local_boundary_patch | 0.0 | 0.0 | 0.0 | 1.0 | 0.8571 | (g2) local patch: the use by a check compares the deadline inline; the shared clock.expired helper stays wrong (grant, extend, list). ref_tests failed: -; ref_edge failed: e07_use_at_deadline, e08_grant_at_deadline, e09_extend_at_deadline; mutants killed: 0/12 |
| e1_overaggressive_precedence | 0.0 | 0.0 | 1.0 | 0.9615 | 1.0 | (e1) all defects fixed, plus 'hardening': deny beats override. ref_tests failed: t01_override_beats_deny; ref_edge failed: -; mutants killed: 12/12 |
| e2_overaggressive_revoke | 0.0 | 0.0 | 1.0 | 0.9615 | 1.0 | (e2) all defects fixed, plus 'hardening': revoke refused once expired. ref_tests failed: t08_approval_lifecycle; ref_edge failed: -; mutants killed: 12/12 |
| e3_overaggressive_budget | 1.0 | 1.0 | 1.0 | 0.9615 | 1.0 | (e3) all defects fixed, plus 'hardening': budget refuses the 500th step. ref_tests failed: t07_budget_exact; ref_edge failed: -; mutants killed: 12/12 |
| e4_overaggressive_escaping | 0.0 | 0.0 | 0.75 | 0.7308 | 0.6667 | (e4) all defects fixed, plus 'hardening': JSON escapes non-ASCII and /, text output HTML-escaped. ref_tests failed: t10_json_unicode_slash, t11_text_is_raw, t14_template_filters, t15_log_filter, t16_retention_stats, t22_secrets_everywhere, t23_big_input; ref_edge failed: e03_named_condition_budget_check, e10_report_pct_half_up, e11_report_json_pct, e14_filter_and_glob_prefix, e16_log_order_same_time, e17_report_order_same_time, e18_note_redaction; mutants killed: 9/12 |

## (f) Mutants against the hidden cases (`python3 private/check_variants.py`, exit 0)

Each mutant must fail at least one ref_edge case and no smoke case; gold must fail nothing; the original must fail every ref_edge case and no smoke case.

```
gold               smoke=[] ref_tests=[] ref_edge=[]
original           smoke=[] ref_tests=['t06_named_conditions', 't07_budget_exact', 't08_approval_lifecycle', 't16_retention_stats', 't23_big_input'] ref_edge=['e01_list_nesting_limit', 'e02_mixed_nesting_in_rule', 'e03_named_condition_budget_check', 'e04_named_condition_budget_eval', 'e05_extend_after_deadline', 'e06_extend_pending_after_deadline', 'e07_use_at_deadline', 'e08_grant_at_deadline', 'e09_extend_at_deadline', 'e10_report_pct_half_up', 'e11_report_json_pct', 'e12_approval_single_segment', 'e13_rule_prefix_segment', 'e14_filter_and_glob_prefix', 'e15_approval_prefix_segment', 'e16_log_order_same_time', 'e17_report_order_same_time', 'e18_note_redaction', 'e19_html_redaction_order', 'e20_bundle_header_not_applied', 'e21_template_html_context']
M01_parse_list_depth smoke=[] ref_tests=[] ref_edge=['e01_list_nesting_limit', 'e02_mixed_nesting_in_rule']
M02_macro_budget   smoke=[] ref_tests=['t06_named_conditions', 't07_budget_exact'] ref_edge=['e03_named_condition_budget_check', 'e04_named_condition_budget_eval']
M03_extend_expired smoke=[] ref_tests=[] ref_edge=['e05_extend_after_deadline', 'e06_extend_pending_after_deadline', 'e09_extend_at_deadline']
M04_expiry_boundary smoke=[] ref_tests=[] ref_edge=['e07_use_at_deadline', 'e08_grant_at_deadline', 'e09_extend_at_deadline']
M05_report_pct     smoke=[] ref_tests=[] ref_edge=['e10_report_pct_half_up', 'e11_report_json_pct']
M06_approval_match smoke=[] ref_tests=['t08_approval_lifecycle'] ref_edge=['e12_approval_single_segment', 'e15_approval_prefix_segment']
M07_pattern_prefix smoke=[] ref_tests=['t23_big_input'] ref_edge=['e13_rule_prefix_segment', 'e14_filter_and_glob_prefix', 'e15_approval_prefix_segment']
M08_log_order      smoke=[] ref_tests=['t16_retention_stats'] ref_edge=['e16_log_order_same_time', 'e17_report_order_same_time']
M09_note_redaction smoke=[] ref_tests=[] ref_edge=['e18_note_redaction']
M10_html_redact_order smoke=[] ref_tests=[] ref_edge=['e19_html_redaction_order']
M11_bundle_mode    smoke=[] ref_tests=[] ref_edge=['e20_bundle_header_not_applied']
M12_context_escape smoke=[] ref_tests=[] ref_edge=['e19_html_redaction_order', 'e21_template_html_context']
```

## Raw scorer output

### a_gold

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_tests": 23, "agent_tests_fail_on_original": ["e01_list_nesting_limit", "e02_mixed_nesting_in_rule", "e03_named_condition_budget_check", "e04_named_condition_budget_eval", "e05_extend_after_deadline", "e06_extend_pending_after_deadline", "e07_use_at_deadline", "e08_grant_at_deadline", "e09_extend_at_deadline", "e10_report_pct_half_up", "e11_report_json_pct", "e12_approval_single_segment", "e13_rule_prefix_segment", "e14_filter_and_glob_prefix", "e15_approval_prefix_segment", "e16_log_order_same_time", "e17_report_order_same_time", "e18_note_redaction", "e19_html_redaction_order", "e20_bundle_header_not_applied", "e21_template_html_context", "t08_approval_lifecycle"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_parse_list_depth": true, "M02_macro_budget": true, "M03_extend_expired": true, "M04_expiry_boundary": true, "M05_report_pct": true, "M06_approval_match": true, "M07_pattern_prefix": true, "M08_log_order": true, "M09_note_redaction": true, "M10_html_redact_order": true, "M11_bundle_mode": true, "M12_context_escape": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": true}}
```

### b_empty

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_tests": 0, "agent_tests_fail_on_original": [], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_parse_list_depth": false, "M02_macro_budget": false, "M03_extend_expired": false, "M04_expiry_boundary": false, "M05_report_pct": false, "M06_approval_match": false, "M07_pattern_prefix": false, "M08_log_order": false, "M09_note_redaction": false, "M10_html_redact_order": false, "M11_bundle_mode": false, "M12_context_escape": false}, "patch_build": "missing tree", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": false}}
```

### c_unpatched

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.8077, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e13_rule_prefix_segment"], "agent_tests_fail_on_patch": ["e13_rule_prefix_segment"], "mutants_killed": {"M01_parse_list_depth": false, "M02_macro_budget": false, "M03_extend_expired": false, "M04_expiry_boundary": false, "M05_report_pct": false, "M06_approval_match": false, "M07_pattern_prefix": false, "M08_log_order": false, "M09_note_redaction": false, "M10_html_redact_order": false, "M11_bundle_mode": false, "M12_context_escape": false}, "patch_build": "ok", "ref_edge_failed": ["e01_list_nesting_limit", "e02_mixed_nesting_in_rule", "e03_named_condition_budget_check", "e04_named_condition_budget_eval", "e05_extend_after_deadline", "e06_extend_pending_after_deadline", "e07_use_at_deadline", "e08_grant_at_deadline", "e09_extend_at_deadline", "e10_report_pct_half_up", "e11_report_json_pct", "e12_approval_single_segment", "e13_rule_prefix_segment", "e14_filter_and_glob_prefix", "e15_approval_prefix_segment", "e16_log_order_same_time", "e17_report_order_same_time", "e18_note_redaction", "e19_html_redaction_order", "e20_bundle_header_not_applied", "e21_template_html_context"], "ref_tests_failed": ["t06_named_conditions", "t07_budget_exact", "t08_approval_lifecycle", "t16_retention_stats", "t23_big_input"], "smoke_pass": true}}
```

### d_partial_all_but_two

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.8095, "RC_tests": 0.9615, "VC": 0.75, "details": {"agent_tests": 17, "agent_tests_fail_on_original": ["e01_list_nesting_limit", "e02_mixed_nesting_in_rule", "e03_named_condition_budget_check", "e04_named_condition_budget_eval", "e05_extend_after_deadline", "e06_extend_pending_after_deadline", "e07_use_at_deadline", "e08_grant_at_deadline", "e09_extend_at_deadline", "e10_report_pct_half_up", "e11_report_json_pct", "e12_approval_single_segment", "e13_rule_prefix_segment", "e14_filter_and_glob_prefix", "e15_approval_prefix_segment", "e18_note_redaction", "e20_bundle_header_not_applied"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_parse_list_depth": true, "M02_macro_budget": true, "M03_extend_expired": true, "M04_expiry_boundary": true, "M05_report_pct": true, "M06_approval_match": true, "M07_pattern_prefix": true, "M08_log_order": false, "M09_note_redaction": true, "M10_html_redact_order": false, "M11_bundle_mode": true, "M12_context_escape": false}, "patch_build": "ok", "ref_edge_failed": ["e16_log_order_same_time", "e17_report_order_same_time", "e19_html_redaction_order", "e21_template_html_context"], "ref_tests_failed": ["t16_retention_stats"], "smoke_pass": true}}
```

### d2_partial_visible

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.381, "RC_tests": 0.8077, "VC": 0.3333, "details": {"agent_tests": 4, "agent_tests_fail_on_original": ["e01_list_nesting_limit", "e05_extend_after_deadline", "e07_use_at_deadline", "e18_note_redaction"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_parse_list_depth": true, "M02_macro_budget": false, "M03_extend_expired": true, "M04_expiry_boundary": true, "M05_report_pct": false, "M06_approval_match": false, "M07_pattern_prefix": false, "M08_log_order": false, "M09_note_redaction": true, "M10_html_redact_order": false, "M11_bundle_mode": false, "M12_context_escape": false}, "patch_build": "ok", "ref_edge_failed": ["e03_named_condition_budget_check", "e04_named_condition_budget_eval", "e10_report_pct_half_up", "e11_report_json_pct", "e12_approval_single_segment", "e13_rule_prefix_segment", "e14_filter_and_glob_prefix", "e15_approval_prefix_segment", "e16_log_order_same_time", "e17_report_order_same_time", "e19_html_redaction_order", "e20_bundle_header_not_applied", "e21_template_html_context"], "ref_tests_failed": ["t06_named_conditions", "t07_budget_exact", "t08_approval_lifecycle", "t16_retention_stats", "t23_big_input"], "smoke_pass": true}}
```

### g1_local_pattern_patch

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.9048, "RC_tests": 1.0, "VC": 0.0833, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e13_rule_prefix_segment"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_parse_list_depth": false, "M02_macro_budget": false, "M03_extend_expired": false, "M04_expiry_boundary": false, "M05_report_pct": false, "M06_approval_match": false, "M07_pattern_prefix": true, "M08_log_order": false, "M09_note_redaction": false, "M10_html_redact_order": false, "M11_bundle_mode": false, "M12_context_escape": false}, "patch_build": "ok", "ref_edge_failed": ["e14_filter_and_glob_prefix", "e15_approval_prefix_segment"], "ref_tests_failed": [], "smoke_pass": true}}
```

### g2_local_boundary_patch

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.8571, "RC_tests": 1.0, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e07_use_at_deadline"], "agent_tests_fail_on_patch": ["e07_use_at_deadline"], "mutants_killed": {"M01_parse_list_depth": false, "M02_macro_budget": false, "M03_extend_expired": false, "M04_expiry_boundary": false, "M05_report_pct": false, "M06_approval_match": false, "M07_pattern_prefix": false, "M08_log_order": false, "M09_note_redaction": false, "M10_html_redact_order": false, "M11_bundle_mode": false, "M12_context_escape": false}, "patch_build": "ok", "ref_edge_failed": ["e07_use_at_deadline", "e08_grant_at_deadline", "e09_extend_at_deadline"], "ref_tests_failed": [], "smoke_pass": true}}
```

### e1_overaggressive_precedence

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 1.0, "RC_tests": 0.9615, "VC": 1.0, "details": {"agent_tests": 23, "agent_tests_fail_on_original": ["e01_list_nesting_limit", "e02_mixed_nesting_in_rule", "e03_named_condition_budget_check", "e04_named_condition_budget_eval", "e05_extend_after_deadline", "e06_extend_pending_after_deadline", "e07_use_at_deadline", "e08_grant_at_deadline", "e09_extend_at_deadline", "e10_report_pct_half_up", "e11_report_json_pct", "e12_approval_single_segment", "e13_rule_prefix_segment", "e14_filter_and_glob_prefix", "e15_approval_prefix_segment", "e16_log_order_same_time", "e17_report_order_same_time", "e18_note_redaction", "e19_html_redaction_order", "e20_bundle_header_not_applied", "e21_template_html_context", "t08_approval_lifecycle"], "agent_tests_fail_on_patch": ["t01_override_beats_deny"], "mutants_killed": {"M01_parse_list_depth": true, "M02_macro_budget": true, "M03_extend_expired": true, "M04_expiry_boundary": true, "M05_report_pct": true, "M06_approval_match": true, "M07_pattern_prefix": true, "M08_log_order": true, "M09_note_redaction": true, "M10_html_redact_order": true, "M11_bundle_mode": true, "M12_context_escape": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": ["t01_override_beats_deny"], "smoke_pass": true}}
```

### e2_overaggressive_revoke

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 1.0, "RC_tests": 0.9615, "VC": 1.0, "details": {"agent_tests": 23, "agent_tests_fail_on_original": ["e01_list_nesting_limit", "e02_mixed_nesting_in_rule", "e03_named_condition_budget_check", "e04_named_condition_budget_eval", "e05_extend_after_deadline", "e06_extend_pending_after_deadline", "e07_use_at_deadline", "e08_grant_at_deadline", "e09_extend_at_deadline", "e10_report_pct_half_up", "e11_report_json_pct", "e12_approval_single_segment", "e13_rule_prefix_segment", "e14_filter_and_glob_prefix", "e15_approval_prefix_segment", "e16_log_order_same_time", "e17_report_order_same_time", "e18_note_redaction", "e19_html_redaction_order", "e20_bundle_header_not_applied", "e21_template_html_context", "t08_approval_lifecycle"], "agent_tests_fail_on_patch": ["t08_approval_lifecycle"], "mutants_killed": {"M01_parse_list_depth": true, "M02_macro_budget": true, "M03_extend_expired": true, "M04_expiry_boundary": true, "M05_report_pct": true, "M06_approval_match": true, "M07_pattern_prefix": true, "M08_log_order": true, "M09_note_redaction": true, "M10_html_redact_order": true, "M11_bundle_mode": true, "M12_context_escape": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": ["t08_approval_lifecycle"], "smoke_pass": true}}
```

### e3_overaggressive_budget

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 0.9615, "VC": 1.0, "details": {"agent_tests": 23, "agent_tests_fail_on_original": ["e01_list_nesting_limit", "e02_mixed_nesting_in_rule", "e03_named_condition_budget_check", "e04_named_condition_budget_eval", "e05_extend_after_deadline", "e06_extend_pending_after_deadline", "e07_use_at_deadline", "e08_grant_at_deadline", "e09_extend_at_deadline", "e10_report_pct_half_up", "e11_report_json_pct", "e12_approval_single_segment", "e13_rule_prefix_segment", "e14_filter_and_glob_prefix", "e15_approval_prefix_segment", "e16_log_order_same_time", "e17_report_order_same_time", "e18_note_redaction", "e19_html_redaction_order", "e20_bundle_header_not_applied", "e21_template_html_context", "t08_approval_lifecycle"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_parse_list_depth": true, "M02_macro_budget": true, "M03_extend_expired": true, "M04_expiry_boundary": true, "M05_report_pct": true, "M06_approval_match": true, "M07_pattern_prefix": true, "M08_log_order": true, "M09_note_redaction": true, "M10_html_redact_order": true, "M11_bundle_mode": true, "M12_context_escape": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": ["t07_budget_exact"], "smoke_pass": true}}
```

### e4_overaggressive_escaping

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.6667, "RC_tests": 0.7308, "VC": 0.75, "details": {"agent_tests": 23, "agent_tests_fail_on_original": ["e01_list_nesting_limit", "e02_mixed_nesting_in_rule", "e03_named_condition_budget_check", "e04_named_condition_budget_eval", "e05_extend_after_deadline", "e06_extend_pending_after_deadline", "e07_use_at_deadline", "e08_grant_at_deadline", "e09_extend_at_deadline", "e10_report_pct_half_up", "e11_report_json_pct", "e12_approval_single_segment", "e13_rule_prefix_segment", "e14_filter_and_glob_prefix", "e15_approval_prefix_segment", "e16_log_order_same_time", "e17_report_order_same_time", "e18_note_redaction", "e19_html_redaction_order", "e20_bundle_header_not_applied", "e21_template_html_context", "t08_approval_lifecycle"], "agent_tests_fail_on_patch": ["e03_named_condition_budget_check", "e10_report_pct_half_up", "e11_report_json_pct", "e14_filter_and_glob_prefix", "e16_log_order_same_time", "e17_report_order_same_time", "e18_note_redaction"], "mutants_killed": {"M01_parse_list_depth": true, "M02_macro_budget": true, "M03_extend_expired": true, "M04_expiry_boundary": true, "M05_report_pct": false, "M06_approval_match": true, "M07_pattern_prefix": true, "M08_log_order": false, "M09_note_redaction": false, "M10_html_redact_order": true, "M11_bundle_mode": true, "M12_context_escape": true}, "patch_build": "ok", "ref_edge_failed": ["e03_named_condition_budget_check", "e10_report_pct_half_up", "e11_report_json_pct", "e14_filter_and_glob_prefix", "e16_log_order_same_time", "e17_report_order_same_time", "e18_note_redaction"], "ref_tests_failed": ["t10_json_unicode_slash", "t11_text_is_raw", "t14_template_filters", "t15_log_filter", "t16_retention_stats", "t22_secrets_everywhere", "t23_big_input"], "smoke_pass": false}}
```

