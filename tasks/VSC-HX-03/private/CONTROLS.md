# CONTROLS (real scorer output)

Command: `python3 -B private/score_task.py <task_dir> private/controls/<name>/out`; artefacts under `private/controls/` (rebuilt by `private/run_controls.py`).

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge |
|---|---|---|---|---|---|
| a_gold | 1 | 1 | 1.0 | 1.0 | 1.0 |
| b_empty | 0 | 0 | 0.0 | 0.0 | 0.0 |
| c_unpatched | 0 | 0 | 0.0 | 0.9 | 0.0 |
| d_partial_visible_sites | 1 | 1 | 0.375 | 0.95 | 0.4091 |
| e_overaggressive | 0 | 0 | 0.125 | 0.35 | 0.8182 |
| f_import_split_only | 0 | 0 | 0.125 | 0.95 | 0.8636 |
| g_import_normalised_text | 0 | 0 | 0.125 | 1.0 | 0.9091 |
| h_bundle_prefix_test | 1 | 1 | 0.125 | 1.0 | 0.9545 |
| i_asset_final_only | 1 | 1 | 0.125 | 1.0 | 0.9545 |
| j_cache_disabled | 0 | 0 | 0.125 | 0.85 | 0.9545 |
| k_all_but_tenant_name | 1 | 1 | 0.875 | 1.0 | 0.9091 |
| l_all_but_asset_lookup | 1 | 1 | 0.875 | 1.0 | 0.9091 |

## a_gold: gold as agent output; tests = all ref_edge cases with gold output
```
{"IC_fix": 1, "IC_tests": 1, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_fail_on_original": 22, "agent_fail_on_patch": 0, "agent_tests": 22, "mutants": 8, "mutants_killed": 8, "patch_builds": true, "ref_edge_failed": [], "ref_tests_failed": [], "smoke_fail_on_patch": 0}}
```

## b_empty: empty out/
```
{"IC_fix": 0, "IC_tests": 0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_fail_on_original": 0, "agent_fail_on_patch": 0, "agent_tests": 0, "mutants": 8, "mutants_killed": 0, "patch_builds": false, "ref_edge_failed": [], "ref_tests_failed": [], "smoke_fail_on_patch": 1}}
```

## c_unpatched: unpatched source as the patch + one test (e09)
```
{"IC_fix": 0, "IC_tests": 0, "RC_edge": 0.0, "RC_tests": 0.9, "VC": 0.0, "details": {"agent_fail_on_original": 1, "agent_fail_on_patch": 1, "agent_tests": 1, "mutants": 8, "mutants_killed": 0, "patch_builds": true, "ref_edge_failed": ["e01_dynamic_include_into_other_tenant", "e02_dynamic_include_through_link_out", "e03_dynamic_include_missing_outside", "e04_bundle_import_through_link_out", "e05_bundle_import_sibling_tenant", "e06_bundle_import_backslash_out", "e07_cache_same_page_two_tenants", "e08_cache_same_page_different_partials", "e09_import_member_with_backslashes", "e10_import_member_with_trailing_spaces", "e11_import_member_outside_tenant", "e12_import_into_theme_folder_with_link_out", "e13_rename_plugin_into_src", "e14_rename_plugin_outside_tenant", "e15_rename_plugin_backslash_and_dots", "e16_asset_case_fold_through_link_out", "e17_asset_case_fold_file_link_out", "e18_tenant_name_of_only_dots", "e19_tenant_name_with_trailing_dot", "e20_toc_after_other_tenant_export", "e21_toc_other_tenant_same_size_archive", "e22_toc_after_both_tenants_export"], "ref_tests_failed": ["t08_backslash_import_in_bundle", "t11_export_toc_import_valid_names"], "smoke_fail_on_patch": 0}}
```

## d_partial_visible_sites: naive partial fix: only the three most visible check sites (dynamic include, bundle @import, rename hook) fixed; tests e01 e04 e13
```
{"IC_fix": 1, "IC_tests": 1, "RC_edge": 0.4091, "RC_tests": 0.95, "VC": 0.375, "details": {"agent_fail_on_original": 3, "agent_fail_on_patch": 0, "agent_tests": 3, "mutants": 8, "mutants_killed": 3, "patch_builds": true, "ref_edge_failed": ["e07_cache_same_page_two_tenants", "e08_cache_same_page_different_partials", "e09_import_member_with_backslashes", "e10_import_member_with_trailing_spaces", "e11_import_member_outside_tenant", "e12_import_into_theme_folder_with_link_out", "e16_asset_case_fold_through_link_out", "e17_asset_case_fold_file_link_out", "e18_tenant_name_of_only_dots", "e19_tenant_name_with_trailing_dot", "e20_toc_after_other_tenant_export", "e21_toc_other_tenant_same_size_archive", "e22_toc_after_both_tenants_export"], "ref_tests_failed": ["t11_export_toc_import_valid_names"], "smoke_fail_on_patch": 0}}
```

## e_overaggressive: over-aggressive fix: gold, but any '..' component or backslash is refused, tenant names may not contain dots, render cache off; tests e01 e09
```
{"IC_fix": 0, "IC_tests": 0, "RC_edge": 0.8182, "RC_tests": 0.35, "VC": 0.125, "details": {"agent_fail_on_original": 2, "agent_fail_on_patch": 1, "agent_tests": 2, "mutants": 8, "mutants_killed": 1, "patch_builds": true, "ref_edge_failed": ["e07_cache_same_page_two_tenants", "e09_import_member_with_backslashes", "e13_rename_plugin_into_src", "e15_rename_plugin_backslash_and_dots"], "ref_tests_failed": ["t02_dotdot_that_stays_inside", "t04_portable_names_and_separators", "t06_dynamic_includes_inside", "t07_bundle_imports", "t08_backslash_import_in_bundle", "t09_rename_plugin_inside", "t10_copy_plugin", "t11_export_toc_import_valid_names", "t12_cache_behaviour", "t13_multi_tenant_switching", "t16_big_site_order_and_cache", "t17_layout_chain", "t20_plugins_denied_by_existing_checks"], "smoke_fail_on_patch": 1}}
```

## f_import_split_only: trap: gold, but IMPORT only adds backslash splitting to the raw '..' test; tests e09 e11
```
{"IC_fix": 0, "IC_tests": 0, "RC_edge": 0.8636, "RC_tests": 0.95, "VC": 0.125, "details": {"agent_fail_on_original": 2, "agent_fail_on_patch": 1, "agent_tests": 2, "mutants": 8, "mutants_killed": 1, "patch_builds": true, "ref_edge_failed": ["e10_import_member_with_trailing_spaces", "e11_import_member_outside_tenant", "e12_import_into_theme_folder_with_link_out"], "ref_tests_failed": ["t11_export_toc_import_valid_names"], "smoke_fail_on_patch": 0}}
```

## g_import_normalised_text: trap: gold, but IMPORT tests the normalised member text (no links); tests e09 e10 e11
```
{"IC_fix": 0, "IC_tests": 0, "RC_edge": 0.9091, "RC_tests": 1.0, "VC": 0.125, "details": {"agent_fail_on_original": 3, "agent_fail_on_patch": 1, "agent_tests": 3, "mutants": 8, "mutants_killed": 1, "patch_builds": true, "ref_edge_failed": ["e11_import_member_outside_tenant", "e12_import_into_theme_folder_with_link_out"], "ref_tests_failed": [], "smoke_fail_on_patch": 0}}
```

## h_bundle_prefix_test: trap: gold, but bundle imports use realpath + startswith(tenant root); test e04
```
{"IC_fix": 1, "IC_tests": 1, "RC_edge": 0.9545, "RC_tests": 1.0, "VC": 0.125, "details": {"agent_fail_on_original": 1, "agent_fail_on_patch": 0, "agent_tests": 1, "mutants": 8, "mutants_killed": 1, "patch_builds": true, "ref_edge_failed": ["e05_bundle_import_sibling_tenant"], "ref_tests_failed": [], "smoke_fail_on_patch": 0}}
```

## i_asset_final_only: trap: gold, but the case-insensitive asset lookup checks only the final file; test e17
```
{"IC_fix": 1, "IC_tests": 1, "RC_edge": 0.9545, "RC_tests": 1.0, "VC": 0.125, "details": {"agent_fail_on_original": 1, "agent_fail_on_patch": 0, "agent_tests": 1, "mutants": 8, "mutants_killed": 1, "patch_builds": true, "ref_edge_failed": ["e16_asset_case_fold_through_link_out"], "ref_tests_failed": [], "smoke_fail_on_patch": 0}}
```

## j_cache_disabled: over-aggressive isolation fix: gold, but cached renders are never reused; tests e07 e08
```
{"IC_fix": 0, "IC_tests": 0, "RC_edge": 0.9545, "RC_tests": 0.85, "VC": 0.125, "details": {"agent_fail_on_original": 2, "agent_fail_on_patch": 1, "agent_tests": 2, "mutants": 8, "mutants_killed": 1, "patch_builds": true, "ref_edge_failed": ["e07_cache_same_page_two_tenants"], "ref_tests_failed": ["t12_cache_behaviour", "t13_multi_tenant_switching", "t16_big_site_order_and_cache"], "smoke_fail_on_patch": 1}}
```

## k_all_but_tenant_name: all variants fixed except the tenant-name canonical check (hardest); all other ref_edge as tests
```
{"IC_fix": 1, "IC_tests": 1, "RC_edge": 0.9091, "RC_tests": 1.0, "VC": 0.875, "details": {"agent_fail_on_original": 20, "agent_fail_on_patch": 0, "agent_tests": 20, "mutants": 8, "mutants_killed": 7, "patch_builds": true, "ref_edge_failed": ["e18_tenant_name_of_only_dots", "e19_tenant_name_with_trailing_dot"], "ref_tests_failed": [], "smoke_fail_on_patch": 0}}
```

## l_all_but_asset_lookup: all variants fixed except the case-insensitive asset lookup; all other ref_edge as tests
```
{"IC_fix": 1, "IC_tests": 1, "RC_edge": 0.9091, "RC_tests": 1.0, "VC": 0.875, "details": {"agent_fail_on_original": 20, "agent_fail_on_patch": 0, "agent_tests": 20, "mutants": 8, "mutants_killed": 7, "patch_builds": true, "ref_edge_failed": ["e16_asset_case_fold_through_link_out", "e17_asset_case_fold_file_link_out"], "ref_tests_failed": [], "smoke_fail_on_patch": 0}}
```

## Reading
* (a) gold as agent output: all five factors 1.0 (22 tests, 8/8 mutants killed).
* (b) empty out/: IC_tests 0, VC 0 (and IC_fix 0, RC 0: no patch).
* (c) unpatched source as patch + e09: IC_tests 0 and IC_fix 0 (its own test fails on the patch); RC_edge 0.
* (d) naive partial fix of the three most visible check sites: RC_edge 0.41 < 1 (cache, import, asset, tenant-name
  and catalogue variants remain).
* (e) over-aggressive path rules + cache off: RC_tests 0.35 < 1 (13 valid-behaviour cases broken, smoke s4 broken).
* (f), (g) IMPORT partial fixes: RC_edge 0.86 / 0.91 < 1 (trailing-space components, links in the theme folder,
  wrong refusal reason).
* (h) bundle realpath + plain prefix test: RC_edge 0.95 < 1 (sibling tenant `acme2`).
* (i) asset lookup re-checks only the final file: RC_edge 0.95 < 1 (folder outside listed, exit 86).
* (j) render cache disabled: RC_tests 0.85 < 1 and smoke fails (documented cached counts).
* (k), (l) all variants fixed except the hardest ones (tenant-name canonical check; case-insensitive asset lookup):
  RC_edge 0.91 < 1 and VC 0.875 with the other 20 edge cases as tests.

## Mutants against the hidden suites (`python3 private/check_matrix.py`)
```
gold                              smoke=[] tests=[] edge=[]
original                          smoke=[] tests=['t08', 't11'] edge=[all 22: e01..e22]
m1_dynamic_include                smoke=[] tests=[] edge=['e01', 'e02', 'e03']
m2_bundle_import_text_check       smoke=[] tests=['t08'] edge=['e04', 'e05', 'e06']
m3_cache_key_without_tenant       smoke=[] tests=[] edge=['e07', 'e08']
m4_import_member_raw_check        smoke=[] tests=['t11'] edge=['e09', 'e10', 'e11', 'e12']
m5_output_path_hook_unchecked     smoke=[] tests=[] edge=['e13', 'e14', 'e15']
m6_asset_folded_lookup_unchecked  smoke=[] tests=[] edge=['e16', 'e17']
m7_tenant_name_not_canonical      smoke=[] tests=[] edge=['e18', 'e19']
m8_export_catalog_shared          smoke=[] tests=[] edge=['e20', 'e21', 'e22']
```
Every mutant fails at least one ref_edge case, so VC = 1 is reachable. How the original fails: exit 86 with
`INVARIANT:` in e01, e02, e04, e05, e07, e08, e11, e12, e14, e16, e17; wrong stdout (writes outside the area,
leaked data, wrong acceptance, `not found` instead of DENIED) in the others.
