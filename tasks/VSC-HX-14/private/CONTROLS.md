# Controls (real scorer output, `python3 private/score_task.py <task> private/controls/<name>`)

Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with `sh private/build_private.sh && python3 private/run_controls.py`.

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |
|---|---|---|---|---|---|---|
| a_original | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | (a) unpatched source as patch, plus one correct test. ref_tests failed: -; ref_edge failed: e01_civil_leap_day_2000, e02_civil_leap_days_other_cycles, e03_category_backslash, e04_category_backslash_import_edit, e05_varint_duration_values, e06_varint_clock_zone_skip_values, e07_offset_negative_minutes, e08_offset_negative_event_edit, e09_weekly_every2_midweek_start, e10_weekly_every_late_week_start, e11_snap_carry_into_next_day, e12_snap_carry_events, e13_agenda_ties_multi_number_ids, e14_agenda_ties_text_after_number, e15_reference_maximum, e16_reference_before_maximum, e17_move_drops_stale_skips, e18_move_drops_stale_skips_monthly, e19_title_long_blank_runs, e20_session_calendar_values, e21_session_codecs, e22_session_ordering_state; mutants killed: 0/10 |
| b_gold | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | (b) gold as patch; every ref_edge plus two ref_tests as agent tests. ref_tests failed: -; ref_edge failed: -; mutants killed: 10/10 |
| c_empty | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | (c) empty out/. ref_tests failed: -; ref_edge failed: -; mutants killed: 0/10 |
| d_partial | 1.0 | 1.0 | 0.8 | 1.0 | 0.7273 | (d) every defect fixed except the reference width at the maximum and the stale skips after an event move; one test per fixed defect. ref_tests failed: -; ref_edge failed: e15_reference_maximum, e16_reference_before_maximum, e17_move_drops_stale_skips, e18_move_drops_stale_skips_monthly, e21_session_codecs, e22_session_ordering_state; mutants killed: 8/10 |
| e_overaggressive | 0.0 | 0.0 | 0.0 | 0.4643 | 0.3636 | (e) gold plus over-fixing: titles collapse every whitespace character (NBSP too), offset 0 prints Z, a yearly Feb 29 event lands on Mar 1. ref_tests failed: t01_daily_every_count, t06_yearly_leap_day, t07_count_includes_skips, t13_offsets, t14_titles, t15_text_records, t17_references, t18_skip_pruning_by_rule, t19_move_keeps_valid_skips, t21_snap_half_up, t23_stats_categories, t25_session_a, t26_session_b, t27_session_c, t28_long_ordinary; ref_edge failed: e01_civil_leap_day_2000, e02_civil_leap_days_other_cycles, e03_category_backslash, e04_category_backslash_import_edit, e05_varint_duration_values, e07_offset_negative_minutes, e12_snap_carry_events, e15_reference_maximum, e17_move_drops_stale_skips, e18_move_drops_stale_skips_monthly, e19_title_long_blank_runs, e20_session_calendar_values, e21_session_codecs, e22_session_ordering_state; mutants killed: 0/10 |
| e2_overaggressive_listings | 1.0 | 0.0 | 0.2 | 0.7857 | 0.8182 | (e2) gold plus over-fixing: busy merges only overlapping spans (touching spans stay apart), stale-skip pruning keeps the last skip. ref_tests failed: t10_busy_touching, t18_skip_pruning_by_rule, t25_session_a, t26_session_b, t27_session_c, t28_long_ordinary; ref_edge failed: e17_move_drops_stale_skips, e18_move_drops_stale_skips_monthly, e20_session_calendar_values, e22_session_ordering_state; mutants killed: 2/10 |
| g_check_disabled | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | (g) all defects kept, self-check disabled (return at top of full_check). ref_tests failed: -; ref_edge failed: e01_civil_leap_day_2000, e02_civil_leap_days_other_cycles, e03_category_backslash, e04_category_backslash_import_edit, e05_varint_duration_values, e06_varint_clock_zone_skip_values, e07_offset_negative_minutes, e08_offset_negative_event_edit, e09_weekly_every2_midweek_start, e10_weekly_every_late_week_start, e11_snap_carry_into_next_day, e12_snap_carry_events, e13_agenda_ties_multi_number_ids, e14_agenda_ties_text_after_number, e15_reference_maximum, e16_reference_before_maximum, e17_move_drops_stale_skips, e18_move_drops_stale_skips_monthly, e19_title_long_blank_runs, e20_session_calendar_values, e21_session_codecs, e22_session_ordering_state; mutants killed: 0/10 |

## (f) Mutants against smoke and ref_edge

Each mutant is gold with exactly one defect brought back (`python3 private/check_variants.py` gives the same data plus ref_tests).

| Mutant | smoke failed | ref_edge failed |
|---|---|---|
| M01_civil_cycle_end | none | e01_civil_leap_day_2000, e02_civil_leap_days_other_cycles, e20_session_calendar_values |
| M02_category_backslash | none | e03_category_backslash, e04_category_backslash_import_edit, e21_session_codecs |
| M03_varint_boundary | none | e05_varint_duration_values, e06_varint_clock_zone_skip_values, e21_session_codecs |
| M04_offset_sign | none | e07_offset_negative_minutes, e08_offset_negative_event_edit, e20_session_calendar_values |
| M05_weekly_anchor | none | e09_weekly_every2_midweek_start, e10_weekly_every_late_week_start, e22_session_ordering_state |
| M06_snap_carry | none | e01_civil_leap_day_2000, e11_snap_carry_into_next_day, e12_snap_carry_events, e20_session_calendar_values |
| M07_natural_ids | none | e13_agenda_ties_multi_number_ids, e14_agenda_ties_text_after_number, e22_session_ordering_state |
| M08_ref_width | none | e15_reference_maximum, e16_reference_before_maximum, e21_session_codecs |
| M09_move_skips | none | e17_move_drops_stale_skips, e18_move_drops_stale_skips_monthly, e22_session_ordering_state |
| M10_title_blanks | none | e19_title_long_blank_runs, e20_session_calendar_values |

## Raw scorer output

### a_original

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 1.0, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_civil_leap_day_2000"], "agent_tests_fail_on_patch": ["e01_civil_leap_day_2000"], "mutants_killed": {"M01_civil_cycle_end": false, "M02_category_backslash": false, "M03_varint_boundary": false, "M04_offset_sign": false, "M05_weekly_anchor": false, "M06_snap_carry": false, "M07_natural_ids": false, "M08_ref_width": false, "M09_move_skips": false, "M10_title_blanks": false}, "patch_build": "ok", "ref_edge_failed": ["e01_civil_leap_day_2000", "e02_civil_leap_days_other_cycles", "e03_category_backslash", "e04_category_backslash_import_edit", "e05_varint_duration_values", "e06_varint_clock_zone_skip_values", "e07_offset_negative_minutes", "e08_offset_negative_event_edit", "e09_weekly_every2_midweek_start", "e10_weekly_every_late_week_start", "e11_snap_carry_into_next_day", "e12_snap_carry_events", "e13_agenda_ties_multi_number_ids", "e14_agenda_ties_text_after_number", "e15_reference_maximum", "e16_reference_before_maximum", "e17_move_drops_stale_skips", "e18_move_drops_stale_skips_monthly", "e19_title_long_blank_runs", "e20_session_calendar_values", "e21_session_codecs", "e22_session_ordering_state"], "ref_tests_failed": [], "smoke_pass": true}}
```

### b_gold

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_tests": 24, "agent_tests_fail_on_original": ["e01_civil_leap_day_2000", "e02_civil_leap_days_other_cycles", "e03_category_backslash", "e04_category_backslash_import_edit", "e05_varint_duration_values", "e06_varint_clock_zone_skip_values", "e07_offset_negative_minutes", "e08_offset_negative_event_edit", "e09_weekly_every2_midweek_start", "e10_weekly_every_late_week_start", "e11_snap_carry_into_next_day", "e12_snap_carry_events", "e13_agenda_ties_multi_number_ids", "e14_agenda_ties_text_after_number", "e15_reference_maximum", "e16_reference_before_maximum", "e17_move_drops_stale_skips", "e18_move_drops_stale_skips_monthly", "e19_title_long_blank_runs", "e20_session_calendar_values", "e21_session_codecs", "e22_session_ordering_state"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_civil_cycle_end": true, "M02_category_backslash": true, "M03_varint_boundary": true, "M04_offset_sign": true, "M05_weekly_anchor": true, "M06_snap_carry": true, "M07_natural_ids": true, "M08_ref_width": true, "M09_move_skips": true, "M10_title_blanks": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": true}}
```

### c_empty

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_tests": 0, "agent_tests_fail_on_original": [], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_civil_cycle_end": false, "M02_category_backslash": false, "M03_varint_boundary": false, "M04_offset_sign": false, "M05_weekly_anchor": false, "M06_snap_carry": false, "M07_natural_ids": false, "M08_ref_width": false, "M09_move_skips": false, "M10_title_blanks": false}, "patch_build": "missing tree", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": false}}
```

### d_partial

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.7273, "RC_tests": 1.0, "VC": 0.8, "details": {"agent_tests": 8, "agent_tests_fail_on_original": ["e01_civil_leap_day_2000", "e03_category_backslash", "e05_varint_duration_values", "e07_offset_negative_minutes", "e09_weekly_every2_midweek_start", "e11_snap_carry_into_next_day", "e13_agenda_ties_multi_number_ids", "e19_title_long_blank_runs"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_civil_cycle_end": true, "M02_category_backslash": true, "M03_varint_boundary": true, "M04_offset_sign": true, "M05_weekly_anchor": true, "M06_snap_carry": true, "M07_natural_ids": true, "M08_ref_width": false, "M09_move_skips": false, "M10_title_blanks": true}, "patch_build": "ok", "ref_edge_failed": ["e15_reference_maximum", "e16_reference_before_maximum", "e17_move_drops_stale_skips", "e18_move_drops_stale_skips_monthly", "e21_session_codecs", "e22_session_ordering_state"], "ref_tests_failed": [], "smoke_pass": true}}
```

### e_overaggressive

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.3636, "RC_tests": 0.4643, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e03_category_backslash"], "agent_tests_fail_on_patch": ["e03_category_backslash"], "mutants_killed": {"M01_civil_cycle_end": false, "M02_category_backslash": false, "M03_varint_boundary": false, "M04_offset_sign": false, "M05_weekly_anchor": false, "M06_snap_carry": false, "M07_natural_ids": false, "M08_ref_width": false, "M09_move_skips": false, "M10_title_blanks": false}, "patch_build": "ok", "ref_edge_failed": ["e01_civil_leap_day_2000", "e02_civil_leap_days_other_cycles", "e03_category_backslash", "e04_category_backslash_import_edit", "e05_varint_duration_values", "e07_offset_negative_minutes", "e12_snap_carry_events", "e15_reference_maximum", "e17_move_drops_stale_skips", "e18_move_drops_stale_skips_monthly", "e19_title_long_blank_runs", "e20_session_calendar_values", "e21_session_codecs", "e22_session_ordering_state"], "ref_tests_failed": ["t01_daily_every_count", "t06_yearly_leap_day", "t07_count_includes_skips", "t13_offsets", "t14_titles", "t15_text_records", "t17_references", "t18_skip_pruning_by_rule", "t19_move_keeps_valid_skips", "t21_snap_half_up", "t23_stats_categories", "t25_session_a", "t26_session_b", "t27_session_c", "t28_long_ordinary"], "smoke_pass": false}}
```

### e2_overaggressive_listings

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.8182, "RC_tests": 0.7857, "VC": 0.2, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_civil_leap_day_2000"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_civil_cycle_end": true, "M02_category_backslash": false, "M03_varint_boundary": false, "M04_offset_sign": false, "M05_weekly_anchor": false, "M06_snap_carry": true, "M07_natural_ids": false, "M08_ref_width": false, "M09_move_skips": false, "M10_title_blanks": false}, "patch_build": "ok", "ref_edge_failed": ["e17_move_drops_stale_skips", "e18_move_drops_stale_skips_monthly", "e20_session_calendar_values", "e22_session_ordering_state"], "ref_tests_failed": ["t10_busy_touching", "t18_skip_pruning_by_rule", "t25_session_a", "t26_session_b", "t27_session_c", "t28_long_ordinary"], "smoke_pass": false}}
```

### g_check_disabled

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 1.0, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_civil_leap_day_2000"], "agent_tests_fail_on_patch": ["e01_civil_leap_day_2000"], "mutants_killed": {"M01_civil_cycle_end": false, "M02_category_backslash": false, "M03_varint_boundary": false, "M04_offset_sign": false, "M05_weekly_anchor": false, "M06_snap_carry": false, "M07_natural_ids": false, "M08_ref_width": false, "M09_move_skips": false, "M10_title_blanks": false}, "patch_build": "ok", "ref_edge_failed": ["e01_civil_leap_day_2000", "e02_civil_leap_days_other_cycles", "e03_category_backslash", "e04_category_backslash_import_edit", "e05_varint_duration_values", "e06_varint_clock_zone_skip_values", "e07_offset_negative_minutes", "e08_offset_negative_event_edit", "e09_weekly_every2_midweek_start", "e10_weekly_every_late_week_start", "e11_snap_carry_into_next_day", "e12_snap_carry_events", "e13_agenda_ties_multi_number_ids", "e14_agenda_ties_text_after_number", "e15_reference_maximum", "e16_reference_before_maximum", "e17_move_drops_stale_skips", "e18_move_drops_stale_skips_monthly", "e19_title_long_blank_runs", "e20_session_calendar_values", "e21_session_codecs", "e22_session_ordering_state"], "ref_tests_failed": [], "smoke_pass": true}}
```

