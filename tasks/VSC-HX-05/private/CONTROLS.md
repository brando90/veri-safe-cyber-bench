# Controls (real scorer output, `python3 private/score_task.py <task> private/controls/<name>`)

Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with `sh private/build_private.sh && python3 private/run_controls.py`.

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |
|---|---|---|---|---|---|---|
| a_gold | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | (a) gold as patch; all ref_edge plus two ref_tests as agent tests. ref_tests failed: -; ref_edge failed: -; mutants killed: 8/8 |
| b_empty | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | (b) empty out/. ref_tests failed: -; ref_edge failed: -; mutants killed: 0/8 |
| c_unpatched | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | (c) unpatched source as patch, plus one correct test. ref_tests failed: -; ref_edge failed: e01_import_services_extra_column, e02_import_customers_extra_column, e03_import_appointments_status_column, e04_audit_export_quoted_name, e05_audit_export_note_and_reason, e06_import_customer_quoted, e07_import_backslash_tab, e08_frontdesk_status_cancelled, e09_custom_role_status_cancelled, e10_billing_imports_customers, e11_billing_imports_other_kinds, e12_custom_importer_role, e13_deny_from_parent_beats_other_parent, e14_child_grant_cannot_undo_ancestor_deny, e15_deny_two_levels_up, e16_deny_reaches_grandchild, e17_grant_reaches_child, e18_tax_report_per_line, e19_tax_report_tsv_discounts, e20_mixed_day; mutants killed: 0/8 |
| d_partial | 1.0 | 1.0 | 0.375 | 1.0 | 0.35 | (d) naive partial fix: import permission, import audit escaping and appt-status cancel permission fixed; header whitelist, audit-export, role resolution, role cache and tax report left. ref_tests failed: -; ref_edge failed: e01_import_services_extra_column, e02_import_customers_extra_column, e03_import_appointments_status_column, e04_audit_export_quoted_name, e05_audit_export_note_and_reason, e13_deny_from_parent_beats_other_parent, e14_child_grant_cannot_undo_ancestor_deny, e15_deny_two_levels_up, e16_deny_reaches_grandchild, e17_grant_reaches_child, e18_tax_report_per_line, e19_tax_report_tsv_discounts, e20_mixed_day; mutants killed: 3/8 |
| e_overaggressive | 0.0 | 0.0 | 0.0 | 0.3125 | 0.45 | (e) over-aggressive: every fix applied, but appt-status always demands appt.cancel and names/notes with double quotes or backslashes are refused. ref_tests failed: t03_frontdesk_status_changes, t04_archive, t05_billing_rounding, t06_reports_plain, t07_special_text_plain, t08_import_valid, t09_big_import, t12_permission_order, t13_export_all, t14_cancel_flows, t16_payments_import_errors; ref_edge failed: e04_audit_export_quoted_name, e05_audit_export_note_and_reason, e06_import_customer_quoted, e07_import_backslash_tab, e08_frontdesk_status_cancelled, e09_custom_role_status_cancelled, e11_billing_imports_other_kinds, e12_custom_importer_role, e18_tax_report_per_line, e19_tax_report_tsv_discounts, e20_mixed_day; mutants killed: 0/8 |
| e2_overaggressive_import | 1.0 | 1.0 | 0.125 | 0.875 | 0.85 | (e2) over-aggressive: import demands every write permission whatever KIND. ref_tests failed: t08_import_valid, t16_payments_import_errors; ref_edge failed: e11_billing_imports_other_kinds, e12_custom_importer_role, e20_mixed_day; mutants killed: 1/8 |
| e3_overaggressive_rounding | 1.0 | 0.0 | 0.125 | 0.6875 | 0.85 | (e3) over-aggressive: money rounding switched to Python round() (half to even). ref_tests failed: t05_billing_rounding, t06_reports_plain, t08_import_valid, t13_export_all, t16_payments_import_errors; ref_edge failed: e05_audit_export_note_and_reason, e11_billing_imports_other_kinds, e12_custom_importer_role; mutants killed: 1/8 |
| f_all_but_role_deny | 1.0 | 1.0 | 0.875 | 1.0 | 0.85 | (f) everything fixed except the hardest variant (deny anywhere in the chain). ref_tests failed: -; ref_edge failed: e13_deny_from_parent_beats_other_parent, e14_child_grant_cannot_undo_ancestor_deny, e15_deny_two_levels_up; mutants killed: 7/8 |
| g_all_but_role_cache | 1.0 | 1.0 | 0.875 | 1.0 | 0.9 | (g) everything fixed except the role-cache variant. ref_tests failed: -; ref_edge failed: e16_deny_reaches_grandchild, e17_grant_reaches_child; mutants killed: 7/8 |

## Raw scorer output

### a_gold

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_tests": 22, "agent_tests_fail_on_original": ["e01_import_services_extra_column", "e02_import_customers_extra_column", "e03_import_appointments_status_column", "e04_audit_export_quoted_name", "e05_audit_export_note_and_reason", "e06_import_customer_quoted", "e07_import_backslash_tab", "e08_frontdesk_status_cancelled", "e09_custom_role_status_cancelled", "e10_billing_imports_customers", "e11_billing_imports_other_kinds", "e12_custom_importer_role", "e13_deny_from_parent_beats_other_parent", "e14_child_grant_cannot_undo_ancestor_deny", "e15_deny_two_levels_up", "e16_deny_reaches_grandchild", "e17_grant_reaches_child", "e18_tax_report_per_line", "e19_tax_report_tsv_discounts", "e20_mixed_day"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M1_import_header": true, "M2_audit_export": true, "M3_audit_bulk": true, "M4_status_cancel": true, "M5_import_perm": true, "M6_role_deny": true, "M7_role_cache": true, "M8_tax_report": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": true}}
```

### b_empty

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_tests": 0, "agent_tests_fail_on_original": [], "agent_tests_fail_on_patch": [], "mutants_killed": {"M1_import_header": false, "M2_audit_export": false, "M3_audit_bulk": false, "M4_status_cancel": false, "M5_import_perm": false, "M6_role_deny": false, "M7_role_cache": false, "M8_tax_report": false}, "patch_build": "missing tree", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": false}}
```

### c_unpatched

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 1.0, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e10_billing_imports_customers"], "agent_tests_fail_on_patch": ["e10_billing_imports_customers"], "mutants_killed": {"M1_import_header": false, "M2_audit_export": false, "M3_audit_bulk": false, "M4_status_cancel": false, "M5_import_perm": false, "M6_role_deny": false, "M7_role_cache": false, "M8_tax_report": false}, "patch_build": "ok", "ref_edge_failed": ["e01_import_services_extra_column", "e02_import_customers_extra_column", "e03_import_appointments_status_column", "e04_audit_export_quoted_name", "e05_audit_export_note_and_reason", "e06_import_customer_quoted", "e07_import_backslash_tab", "e08_frontdesk_status_cancelled", "e09_custom_role_status_cancelled", "e10_billing_imports_customers", "e11_billing_imports_other_kinds", "e12_custom_importer_role", "e13_deny_from_parent_beats_other_parent", "e14_child_grant_cannot_undo_ancestor_deny", "e15_deny_two_levels_up", "e16_deny_reaches_grandchild", "e17_grant_reaches_child", "e18_tax_report_per_line", "e19_tax_report_tsv_discounts", "e20_mixed_day"], "ref_tests_failed": [], "smoke_pass": true}}
```

### d_partial

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.35, "RC_tests": 1.0, "VC": 0.375, "details": {"agent_tests": 3, "agent_tests_fail_on_original": ["e06_import_customer_quoted", "e08_frontdesk_status_cancelled", "e10_billing_imports_customers"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M1_import_header": false, "M2_audit_export": false, "M3_audit_bulk": true, "M4_status_cancel": true, "M5_import_perm": true, "M6_role_deny": false, "M7_role_cache": false, "M8_tax_report": false}, "patch_build": "ok", "ref_edge_failed": ["e01_import_services_extra_column", "e02_import_customers_extra_column", "e03_import_appointments_status_column", "e04_audit_export_quoted_name", "e05_audit_export_note_and_reason", "e13_deny_from_parent_beats_other_parent", "e14_child_grant_cannot_undo_ancestor_deny", "e15_deny_two_levels_up", "e16_deny_reaches_grandchild", "e17_grant_reaches_child", "e18_tax_report_per_line", "e19_tax_report_tsv_discounts", "e20_mixed_day"], "ref_tests_failed": [], "smoke_pass": true}}
```

### e_overaggressive

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.45, "RC_tests": 0.3125, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e08_frontdesk_status_cancelled"], "agent_tests_fail_on_patch": ["e08_frontdesk_status_cancelled"], "mutants_killed": {"M1_import_header": false, "M2_audit_export": false, "M3_audit_bulk": false, "M4_status_cancel": false, "M5_import_perm": false, "M6_role_deny": false, "M7_role_cache": false, "M8_tax_report": false}, "patch_build": "ok", "ref_edge_failed": ["e04_audit_export_quoted_name", "e05_audit_export_note_and_reason", "e06_import_customer_quoted", "e07_import_backslash_tab", "e08_frontdesk_status_cancelled", "e09_custom_role_status_cancelled", "e11_billing_imports_other_kinds", "e12_custom_importer_role", "e18_tax_report_per_line", "e19_tax_report_tsv_discounts", "e20_mixed_day"], "ref_tests_failed": ["t03_frontdesk_status_changes", "t04_archive", "t05_billing_rounding", "t06_reports_plain", "t07_special_text_plain", "t08_import_valid", "t09_big_import", "t12_permission_order", "t13_export_all", "t14_cancel_flows", "t16_payments_import_errors"], "smoke_pass": false}}
```

### e2_overaggressive_import

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.85, "RC_tests": 0.875, "VC": 0.125, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e10_billing_imports_customers"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M1_import_header": false, "M2_audit_export": false, "M3_audit_bulk": false, "M4_status_cancel": false, "M5_import_perm": true, "M6_role_deny": false, "M7_role_cache": false, "M8_tax_report": false}, "patch_build": "ok", "ref_edge_failed": ["e11_billing_imports_other_kinds", "e12_custom_importer_role", "e20_mixed_day"], "ref_tests_failed": ["t08_import_valid", "t16_payments_import_errors"], "smoke_pass": true}}
```

### e3_overaggressive_rounding

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.85, "RC_tests": 0.6875, "VC": 0.125, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e18_tax_report_per_line"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M1_import_header": false, "M2_audit_export": false, "M3_audit_bulk": false, "M4_status_cancel": false, "M5_import_perm": false, "M6_role_deny": false, "M7_role_cache": false, "M8_tax_report": true}, "patch_build": "ok", "ref_edge_failed": ["e05_audit_export_note_and_reason", "e11_billing_imports_other_kinds", "e12_custom_importer_role"], "ref_tests_failed": ["t05_billing_rounding", "t06_reports_plain", "t08_import_valid", "t13_export_all", "t16_payments_import_errors"], "smoke_pass": false}}
```

### f_all_but_role_deny

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.85, "RC_tests": 1.0, "VC": 0.875, "details": {"agent_tests": 17, "agent_tests_fail_on_original": ["e01_import_services_extra_column", "e02_import_customers_extra_column", "e03_import_appointments_status_column", "e04_audit_export_quoted_name", "e05_audit_export_note_and_reason", "e06_import_customer_quoted", "e07_import_backslash_tab", "e08_frontdesk_status_cancelled", "e09_custom_role_status_cancelled", "e10_billing_imports_customers", "e11_billing_imports_other_kinds", "e12_custom_importer_role", "e16_deny_reaches_grandchild", "e17_grant_reaches_child", "e18_tax_report_per_line", "e19_tax_report_tsv_discounts", "e20_mixed_day"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M1_import_header": true, "M2_audit_export": true, "M3_audit_bulk": true, "M4_status_cancel": true, "M5_import_perm": true, "M6_role_deny": false, "M7_role_cache": true, "M8_tax_report": true}, "patch_build": "ok", "ref_edge_failed": ["e13_deny_from_parent_beats_other_parent", "e14_child_grant_cannot_undo_ancestor_deny", "e15_deny_two_levels_up"], "ref_tests_failed": [], "smoke_pass": true}}
```

### g_all_but_role_cache

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.9, "RC_tests": 1.0, "VC": 0.875, "details": {"agent_tests": 18, "agent_tests_fail_on_original": ["e01_import_services_extra_column", "e02_import_customers_extra_column", "e03_import_appointments_status_column", "e04_audit_export_quoted_name", "e05_audit_export_note_and_reason", "e06_import_customer_quoted", "e07_import_backslash_tab", "e08_frontdesk_status_cancelled", "e09_custom_role_status_cancelled", "e10_billing_imports_customers", "e11_billing_imports_other_kinds", "e12_custom_importer_role", "e13_deny_from_parent_beats_other_parent", "e14_child_grant_cannot_undo_ancestor_deny", "e15_deny_two_levels_up", "e18_tax_report_per_line", "e19_tax_report_tsv_discounts", "e20_mixed_day"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M1_import_header": true, "M2_audit_export": true, "M3_audit_bulk": true, "M4_status_cancel": true, "M5_import_perm": true, "M6_role_deny": true, "M7_role_cache": false, "M8_tax_report": true}, "patch_build": "ok", "ref_edge_failed": ["e16_deny_reaches_grandchild", "e17_grant_reaches_child"], "ref_tests_failed": [], "smoke_pass": true}}
```


## Hidden cases vs original and mutants (python3 private/check_variants.py)

```
gold               smoke=[] ref_tests=[] ref_edge=[]
original           smoke=[] ref_tests=[] ref_edge=['e01_import_services_extra_column', 'e02_import_customers_extra_column', 'e03_import_appointments_status_column', 'e04_audit_export_quoted_name', 'e05_audit_export_note_and_reason', 'e06_import_customer_quoted', 'e07_import_backslash_tab', 'e08_frontdesk_status_cancelled', 'e09_custom_role_status_cancelled', 'e10_billing_imports_customers', 'e11_billing_imports_other_kinds', 'e12_custom_importer_role', 'e13_deny_from_parent_beats_other_parent', 'e14_child_grant_cannot_undo_ancestor_deny', 'e15_deny_two_levels_up', 'e16_deny_reaches_grandchild', 'e17_grant_reaches_child', 'e18_tax_report_per_line', 'e19_tax_report_tsv_discounts', 'e20_mixed_day']
M1_import_header   smoke=[] ref_tests=[] ref_edge=['e01_import_services_extra_column', 'e02_import_customers_extra_column', 'e03_import_appointments_status_column']
M2_audit_export    smoke=[] ref_tests=[] ref_edge=['e04_audit_export_quoted_name', 'e05_audit_export_note_and_reason', 'e20_mixed_day']
M3_audit_bulk      smoke=[] ref_tests=[] ref_edge=['e06_import_customer_quoted', 'e07_import_backslash_tab', 'e20_mixed_day']
M4_status_cancel   smoke=[] ref_tests=[] ref_edge=['e08_frontdesk_status_cancelled', 'e09_custom_role_status_cancelled']
M5_import_perm     smoke=[] ref_tests=[] ref_edge=['e10_billing_imports_customers', 'e11_billing_imports_other_kinds', 'e12_custom_importer_role', 'e20_mixed_day']
M6_role_deny       smoke=[] ref_tests=[] ref_edge=['e13_deny_from_parent_beats_other_parent', 'e14_child_grant_cannot_undo_ancestor_deny', 'e15_deny_two_levels_up']
M7_role_cache      smoke=[] ref_tests=[] ref_edge=['e16_deny_reaches_grandchild', 'e17_grant_reaches_child']
M8_tax_report      smoke=[] ref_tests=[] ref_edge=['e18_tax_report_per_line', 'e19_tax_report_tsv_discounts']
```

Original: passes all 5 smoke and 16 ref_tests cases, fails all 20 ref_edge cases. Every mutant fails at least one hidden case (only its own ref_edge cases), so VC = 1 is reachable.
