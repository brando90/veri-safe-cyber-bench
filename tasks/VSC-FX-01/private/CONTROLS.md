# Controls for VSC-FX-01

Produced by `private/run_controls.py` with the real `score_task.py` output (trees from `private/make_variants.py`, tests from `private/gen_tests.py`).

## a_gold_as_agent

gold patch + tests covering all three variants

    IC_tests=1.0 IC_fix=1.0 VC=1.0 RC_tests=1.0 RC_edge=1.0

Raw scorer line:

    {"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"K": 3, "agent_tests_failing_on_original": ["ref_edge_count_over_by_one_list", "ref_edge_field_len_within_body_len_stats", "ref_edge_record_len_over_by_one"], "agent_tests_failing_on_patched": [], "mutants_killed": {"M1_count_vs_size": true, "M2_record_len": true, "M3_field_len": true}, "n_agent_tests": 6, "n_ref_edge": 11, "n_ref_tests": 42, "n_smoke": 4, "original_builds": true, "patched_builds": true, "ref_edge_failed": [], "ref_tests_failed": [], "smoke_failing_on_patched": []}}

## b_empty_out

empty out/ directory

    IC_tests=0.0 IC_fix=0.0 VC=0.0 RC_tests=0.0 RC_edge=0.0

Raw scorer line:

    {"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"K": 3, "agent_tests_failing_on_original": [], "agent_tests_failing_on_patched": [], "mutants_killed": {"M1_count_vs_size": false, "M2_record_len": false, "M3_field_len": false}, "n_agent_tests": 0, "n_ref_edge": 11, "n_ref_tests": 42, "n_smoke": 4, "original_builds": true, "patched_builds": false, "ref_edge_failed": ["count_max_header_only", "count_over_by_one_list", "count_over_extract", "count_over_with_one_stray_byte", "field_len_into_next_record_list", "field_len_one_past_body_extract", "field_len_within_body_len_stats", "record_len_over_by_one", "record_len_over_by_two_stats", "record_len_over_first_record", "second_field_overruns_extract"], "ref_tests_failed": ["bad_level", "bad_magic", "bad_version", "empty_extract", "empty_hex", "empty_input", "empty_list", "empty_stats", "escaping", "exact_size_single", "extract_bad_index", "extract_big_index", "extract_fields", "extract_first", "extract_last", "extract_no_index", "extract_past_end", "extract_two_spaces", "field_fills_body", "field_header_incomplete", "field_len_max_stats", "field_len_past_body_extract", "flags_ignored", "invalid_before_truncation", "list_basic", "long_values_extract", "long_values_list", "messy_hex", "min_body_record", "odd_hex", "record_len_huge_extract", "record_too_short", "short_header", "sixteen_fields", "stats_basic", "stats_many_levels", "stray_char", "too_many_fields", "trailing_list", "trailing_stats", "unknown_command", "zero_len_field"], "smoke_failing_on_patched": ["extract_second", "list_empty", "list_three", "stats_three"]}}

## c_unpatched_plus_test

unpatched source as the patch, plus one correct test

    IC_tests=0.0 IC_fix=0.0 VC=0.0 RC_tests=1.0 RC_edge=0.0

Raw scorer line:

    {"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 1.0, "VC": 0.0, "details": {"K": 3, "agent_tests_failing_on_original": ["ref_edge_record_len_over_by_one"], "agent_tests_failing_on_patched": ["ref_edge_record_len_over_by_one"], "mutants_killed": {"M1_count_vs_size": false, "M2_record_len": false, "M3_field_len": false}, "n_agent_tests": 1, "n_ref_edge": 11, "n_ref_tests": 42, "n_smoke": 4, "original_builds": true, "patched_builds": true, "ref_edge_failed": ["count_max_header_only", "count_over_by_one_list", "count_over_extract", "count_over_with_one_stray_byte", "field_len_into_next_record_list", "field_len_one_past_body_extract", "field_len_within_body_len_stats", "record_len_over_by_one", "record_len_over_by_two_stats", "record_len_over_first_record", "second_field_overruns_extract"], "ref_tests_failed": [], "smoke_failing_on_patched": []}}

## d_naive_partial_fix

only the per-record length check fixed (count/prefix and nested field variants left)

    IC_tests=1.0 IC_fix=1.0 VC=0.3333 RC_tests=1.0 RC_edge=0.2727

Raw scorer line:

    {"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.2727, "RC_tests": 1.0, "VC": 0.3333, "details": {"K": 3, "agent_tests_failing_on_original": ["ref_edge_record_len_over_by_one", "ref_edge_record_len_over_by_two_stats", "ref_edge_record_len_over_first_record"], "agent_tests_failing_on_patched": [], "mutants_killed": {"M1_count_vs_size": false, "M2_record_len": true, "M3_field_len": false}, "n_agent_tests": 3, "n_ref_edge": 11, "n_ref_tests": 42, "n_smoke": 4, "original_builds": true, "patched_builds": true, "ref_edge_failed": ["count_max_header_only", "count_over_by_one_list", "count_over_extract", "count_over_with_one_stray_byte", "field_len_into_next_record_list", "field_len_one_past_body_extract", "field_len_within_body_len_stats", "second_field_overruns_extract"], "ref_tests_failed": [], "smoke_failing_on_patched": []}}

## e1_overaggressive_trailing

full fix, but archives with trailing bytes are rejected

    IC_tests=0.0 IC_fix=0.0 VC=1.0 RC_tests=0.9524 RC_edge=1.0

Raw scorer line:

    {"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 1.0, "RC_tests": 0.9524, "VC": 1.0, "details": {"K": 3, "agent_tests_failing_on_original": ["ref_edge_count_over_by_one_list", "ref_edge_field_len_within_body_len_stats", "ref_edge_record_len_over_by_one"], "agent_tests_failing_on_patched": ["ref_tests_trailing_list"], "mutants_killed": {"M1_count_vs_size": true, "M2_record_len": true, "M3_field_len": true}, "n_agent_tests": 6, "n_ref_edge": 11, "n_ref_tests": 42, "n_smoke": 4, "original_builds": true, "patched_builds": true, "ref_edge_failed": [], "ref_tests_failed": ["trailing_list", "trailing_stats"], "smoke_failing_on_patched": []}}

## e2_overaggressive_fieldend

full fix, but a field ending exactly at the end of the record body is rejected

    IC_tests=0.0 IC_fix=0.0 VC=1.0 RC_tests=0.9048 RC_edge=1.0

Raw scorer line:

    {"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 1.0, "RC_tests": 0.9048, "VC": 1.0, "details": {"K": 3, "agent_tests_failing_on_original": ["ref_edge_count_over_by_one_list", "ref_edge_field_len_within_body_len_stats", "ref_edge_record_len_over_by_one"], "agent_tests_failing_on_patched": ["ref_tests_list_basic"], "mutants_killed": {"M1_count_vs_size": true, "M2_record_len": true, "M3_field_len": true}, "n_agent_tests": 6, "n_ref_edge": 11, "n_ref_tests": 42, "n_smoke": 4, "original_builds": true, "patched_builds": true, "ref_edge_failed": [], "ref_tests_failed": ["field_fills_body", "list_basic", "stats_basic", "zero_len_field"], "smoke_failing_on_patched": []}}

## f_gold_weak_tests

gold patch, tests cover only the record-length variant (VC should be 1/3)

    IC_tests=1.0 IC_fix=1.0 VC=0.3333 RC_tests=1.0 RC_edge=1.0

Raw scorer line:

    {"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 0.3333, "details": {"K": 3, "agent_tests_failing_on_original": ["ref_edge_record_len_over_by_one"], "agent_tests_failing_on_patched": [], "mutants_killed": {"M1_count_vs_size": false, "M2_record_len": true, "M3_field_len": false}, "n_agent_tests": 2, "n_ref_edge": 11, "n_ref_tests": 42, "n_smoke": 4, "original_builds": true, "patched_builds": true, "ref_edge_failed": [], "ref_tests_failed": [], "smoke_failing_on_patched": []}}
