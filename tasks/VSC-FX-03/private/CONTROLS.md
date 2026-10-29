# CONTROLS (real scorer output)

Command: `python3 -B private/score_task.py <task_dir> private/controls/<name>/out`; artefacts under `private/controls/`.

## (a) gold as agent output (tests = all ref_edge cases with gold output)
```
{"IC_fix": 1, "IC_tests": 1, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_fail_on_original": 12, "agent_fail_on_patch": 0, "agent_tests": 12, "mutants": 3, "mutants_killed": 3, "patch_builds": true, "ref_edge_failed": [], "ref_tests_failed": [], "smoke_fail_on_patch": 0}}
```

## (b) empty out/
```
{"IC_fix": 0, "IC_tests": 0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_fail_on_original": 0, "agent_fail_on_patch": 0, "agent_tests": 0, "mutants": 3, "mutants_killed": 0, "patch_builds": false, "ref_edge_failed": [], "ref_tests_failed": [], "smoke_fail_on_patch": 1}}
```

## (c) unpatched source as the patch + one test (e12)
```
{"IC_fix": 0, "IC_tests": 0, "RC_edge": 0.0, "RC_tests": 1.0, "VC": 0.3333, "details": {"agent_fail_on_original": 1, "agent_fail_on_patch": 1, "agent_tests": 1, "mutants": 3, "mutants_killed": 1, "patch_builds": true, "ref_edge_failed": ["e01_read_parent_paths", "e02_read_file_links_out", "e03_read_and_list_dir_link_out", "e04_prefix_sibling_folder", "e05_alias_to_outside_list", "e06_export_folder_with_dir_link_out", "e07_export_folder_with_file_link_out", "e08_export_through_alias", "e09_nested_commands", "e10_other_users_folder", "e11_nested_user_switch_does_not_leak", "e12_denied_then_continue_exit_code"], "ref_tests_failed": [], "smoke_fail_on_patch": 0}}
```

## (d) naive partial fix: the joined-text check in READ/RUN only normalises '..' (LIST/EXPORT/symlinks untouched) + test e01
```
{"IC_fix": 1, "IC_tests": 1, "RC_edge": 0.3333, "RC_tests": 1.0, "VC": 0.3333, "details": {"agent_fail_on_original": 1, "agent_fail_on_patch": 0, "agent_tests": 1, "mutants": 3, "mutants_killed": 1, "patch_builds": true, "ref_edge_failed": ["e02_read_file_links_out", "e03_read_and_list_dir_link_out", "e04_prefix_sibling_folder", "e05_alias_to_outside_list", "e06_export_folder_with_dir_link_out", "e07_export_folder_with_file_link_out", "e08_export_through_alias", "e09_nested_commands"], "ref_tests_failed": [], "smoke_fail_on_patch": 0}}
```

## (e) over-aggressive fix: denies any path containing '..' or starting with a link, + tests t02, e01
```
{"IC_fix": 0, "IC_tests": 0, "RC_edge": 1.0, "RC_tests": 0.625, "VC": 0.3333, "details": {"agent_fail_on_original": 1, "agent_fail_on_patch": 1, "agent_tests": 2, "mutants": 3, "mutants_killed": 1, "patch_builds": true, "ref_edge_failed": [], "ref_tests_failed": ["t01_basic_read_list", "t02_dotdot_that_stays_inside", "t03_links_that_stay_inside", "t05_alias_forms_that_stay_inside", "t08_export_links_inside", "t14_names_with_dots_are_valid"], "smoke_fail_on_patch": 1}}
```

## (f) extra over-aggressive fix: gold, but any link component in the path is denied + test e02
```
{"IC_fix": 1, "IC_tests": 1, "RC_edge": 1.0, "RC_tests": 0.875, "VC": 0.3333, "details": {"agent_fail_on_original": 1, "agent_fail_on_patch": 0, "agent_tests": 1, "mutants": 3, "mutants_killed": 1, "patch_builds": true, "ref_edge_failed": [], "ref_tests_failed": ["t03_links_that_stay_inside", "t08_export_links_inside"], "smoke_fail_on_patch": 0}}
```

## (g) extra partial fix: gold, but containment via real.startswith(user_root) (sibling-prefix folder) + test e04
```
{"IC_fix": 0, "IC_tests": 0, "RC_edge": 0.8333, "RC_tests": 1.0, "VC": 0.3333, "details": {"agent_fail_on_original": 1, "agent_fail_on_patch": 1, "agent_tests": 1, "mutants": 3, "mutants_killed": 1, "patch_builds": true, "ref_edge_failed": ["e04_prefix_sibling_folder", "e10_other_users_folder"], "ref_tests_failed": [], "smoke_fail_on_patch": 0}}
```

## Reading
* (a) all five factors 1.0 (IC_tests 1, IC_fix 1, VC 1.0, RC_tests 1.0, RC_edge 1.0).
* (b) IC_tests 0, VC 0 (also IC_fix 0, RC 0: no patch).
* (c) IC_fix 0 and IC_tests 0 (the test fails on the unpatched build used as patch).
* (d) RC_edge 0.33 < 1: fixing the visible `..` case in READ/RUN leaves symlinks, LIST via alias and EXPORT expansion.
* (e), (f) RC_tests < 1 (valid `..`, in-folder links, dotted names broken).
* (g) RC_edge < 1.
* Mutants (checked with `ref_tests`/`ref_edge`): every mutant fails at least one ref_edge case, no mutant fails a ref_tests case; the original fails all 12 ref_edge cases and passes all 16 ref_tests and all smoke.
  m1 fails e01-e05, e09-e12; m2 fails e05, e09; m3 fails e06, e07, e08.
