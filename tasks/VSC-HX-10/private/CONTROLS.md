# Controls (real scorer output, `python3 private/score_task.py <task> private/controls/<name>`)

Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with `sh private/build_private.sh && python3 private/run_controls.py`.

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |
|---|---|---|---|---|---|---|
| a_original | 0.0 | 0.0 | 0.0 | 0.6538 | 0.0 | (a) unpatched source as patch, plus one correct test. ref_tests failed: t14_hold_id_wrap, t15_settlement_basic, t16_backlog_full, t18_compaction_blocked, t19_long_mixed_a, t20_long_mixed_b, t21_long_mixed_nokeys, t24_long_mixed_noholds, t25_many_accounts; ref_edge failed: e01_reuse_daily_tally, e02_reuse_churn_tallies, e03_epoch_rollover, e04_epoch_keys_batches, e05_compaction_partial_segment, e06_compaction_partial_later, e07_lru_touch, e08_lru_long_mix, e09_slot_reuse_keys, e10_churn_keys, e11_hold_wrap_untimed, e12_hold_wrap_mixed, e13_velocity_hour_edge, e14_velocity_long, e15_entry_reuse_attempts, e16_settlement_long, e17_segment_boundaries, e18_segment_stats_long, e19_hold_long_ttl, e20_holds_long_mixed_ttl; mutants killed: 0/10 |
| b_gold | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | (b) gold as patch; every ref_edge plus two ref_tests as agent tests. ref_tests failed: -; ref_edge failed: -; mutants killed: 10/10 |
| c_empty | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | (c) empty out/. ref_tests failed: -; ref_edge failed: -; mutants killed: 0/10 |
| d_partial | 1.0 | 1.0 | 0.8 | 0.9615 | 0.75 | (d) every variant fixed except the two hardest (compaction folding a segment whose last record is the first unassigned one; hold ids reused for live holds without a ttl); one test per fixed variant. ref_tests failed: t19_long_mixed_a; ref_edge failed: e05_compaction_partial_segment, e06_compaction_partial_later, e11_hold_wrap_untimed, e12_hold_wrap_mixed, e16_settlement_long; mutants killed: 8/10 |
| e_overaggressive | 1.0 | 0.0 | 0.1 | 0.7308 | 0.8 | (e) gold plus 'hardening': slot generation reset to 0 on reuse, reversals counted as debits. ref_tests failed: t03_overdraft_and_funds, t06_reversal_rules, t13_slots_reuse, t19_long_mixed_a, t20_long_mixed_b, t21_long_mixed_nokeys, t24_long_mixed_noholds; ref_edge failed: e01_reuse_daily_tally, e02_reuse_churn_tallies, e09_slot_reuse_keys, e10_churn_keys; mutants killed: 1/10 |
| e2_overaggressive_purge | 0.0 | 0.0 | 0.0 | 0.6923 | 0.9 | (e2) gold plus 'hardening': idempotency keys of an account purged at close, the lowest freed slot reused before fresh ones. ref_tests failed: t06_reversal_rules, t11_idem_reopen_name, t12_idem_eviction, t13_slots_reuse, t19_long_mixed_a, t21_long_mixed_nokeys, t23_close_rules, t24_long_mixed_noholds; ref_edge failed: e09_slot_reuse_keys, e10_churn_keys; mutants killed: 0/10 |
| g_local_seal | 0.0 | 0.0 | 0.0 | 0.8077 | 0.65 | (g) all fixed except the segment seal condition; record lookup made to scan segments so show/check work (segment sizes and compaction timing stay wrong). ref_tests failed: t18_compaction_blocked, t19_long_mixed_a, t20_long_mixed_b, t21_long_mixed_nokeys, t24_long_mixed_noholds; ref_edge failed: e03_epoch_rollover, e04_epoch_keys_batches, e05_compaction_partial_segment, e06_compaction_partial_later, e16_settlement_long, e17_segment_boundaries, e18_segment_stats_long; mutants killed: 0/10 |
| h_local_txid | 0.0 | 0.0 | 0.0 | 1.0 | 0.9 | (h) all fixed except the packed transaction id; the journal index keyed by (epoch, seq) (idempotency replays and batch lines still decode wrong ids after epoch 0). ref_tests failed: -; ref_edge failed: e03_epoch_rollover, e04_epoch_keys_batches; mutants killed: 0/10 |
| i_local_scope | 1.0 | 1.0 | 0.2 | 0.9615 | 1.0 | (i) all fixed except the idempotency scope, which is changed from slot to account name (keys carry over to a later account reusing the name). ref_tests failed: t11_idem_reopen_name; ref_edge failed: -; mutants killed: 2/10 |

## (f) Mutants against smoke and ref_edge

Each mutant is gold with exactly one defect brought back (`python3 private/check_variants.py` gives the same data plus ref_tests).

| Mutant | smoke failed | ref_edge failed |
|---|---|---|
| M01_recycle_limits | none | e01_reuse_daily_tally, e02_reuse_churn_tallies, e09_slot_reuse_keys |
| M02_txid_pack | none | e03_epoch_rollover, e04_epoch_keys_batches |
| M03_compact_covers | none | e05_compaction_partial_segment, e06_compaction_partial_later, e16_settlement_long |
| M04_lru_stamp | none | e07_lru_touch, e08_lru_long_mix |
| M05_idem_scope | none | e09_slot_reuse_keys, e10_churn_keys |
| M06_hold_ids | none | e11_hold_wrap_untimed, e12_hold_wrap_mixed |
| M07_ring_edge | none | e13_velocity_hour_edge, e14_velocity_long |
| M08_entry_attempts | none | e15_entry_reuse_attempts, e16_settlement_long |
| M09_seal | none | e02_reuse_churn_tallies, e03_epoch_rollover, e04_epoch_keys_batches, e05_compaction_partial_segment, e06_compaction_partial_later, e08_lru_long_mix, e10_churn_keys, e12_hold_wrap_mixed, e14_velocity_long, e16_settlement_long, e17_segment_boundaries, e18_segment_stats_long |
| M10_wheel | none | e19_hold_long_ttl, e20_holds_long_mixed_ttl |

## Raw scorer output

### a_original

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.6538, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e13_velocity_hour_edge"], "agent_tests_fail_on_patch": ["e13_velocity_hour_edge"], "mutants_killed": {"M01_recycle_limits": false, "M02_txid_pack": false, "M03_compact_covers": false, "M04_lru_stamp": false, "M05_idem_scope": false, "M06_hold_ids": false, "M07_ring_edge": false, "M08_entry_attempts": false, "M09_seal": false, "M10_wheel": false}, "patch_build": "ok", "ref_edge_failed": ["e01_reuse_daily_tally", "e02_reuse_churn_tallies", "e03_epoch_rollover", "e04_epoch_keys_batches", "e05_compaction_partial_segment", "e06_compaction_partial_later", "e07_lru_touch", "e08_lru_long_mix", "e09_slot_reuse_keys", "e10_churn_keys", "e11_hold_wrap_untimed", "e12_hold_wrap_mixed", "e13_velocity_hour_edge", "e14_velocity_long", "e15_entry_reuse_attempts", "e16_settlement_long", "e17_segment_boundaries", "e18_segment_stats_long", "e19_hold_long_ttl", "e20_holds_long_mixed_ttl"], "ref_tests_failed": ["t14_hold_id_wrap", "t15_settlement_basic", "t16_backlog_full", "t18_compaction_blocked", "t19_long_mixed_a", "t20_long_mixed_b", "t21_long_mixed_nokeys", "t24_long_mixed_noholds", "t25_many_accounts"], "smoke_pass": true}}
```

### b_gold

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_tests": 22, "agent_tests_fail_on_original": ["e01_reuse_daily_tally", "e02_reuse_churn_tallies", "e03_epoch_rollover", "e04_epoch_keys_batches", "e05_compaction_partial_segment", "e06_compaction_partial_later", "e07_lru_touch", "e08_lru_long_mix", "e09_slot_reuse_keys", "e10_churn_keys", "e11_hold_wrap_untimed", "e12_hold_wrap_mixed", "e13_velocity_hour_edge", "e14_velocity_long", "e15_entry_reuse_attempts", "e16_settlement_long", "e17_segment_boundaries", "e18_segment_stats_long", "e19_hold_long_ttl", "e20_holds_long_mixed_ttl"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_recycle_limits": true, "M02_txid_pack": true, "M03_compact_covers": true, "M04_lru_stamp": true, "M05_idem_scope": true, "M06_hold_ids": true, "M07_ring_edge": true, "M08_entry_attempts": true, "M09_seal": true, "M10_wheel": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": true}}
```

### c_empty

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_tests": 0, "agent_tests_fail_on_original": [], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_recycle_limits": false, "M02_txid_pack": false, "M03_compact_covers": false, "M04_lru_stamp": false, "M05_idem_scope": false, "M06_hold_ids": false, "M07_ring_edge": false, "M08_entry_attempts": false, "M09_seal": false, "M10_wheel": false}, "patch_build": "missing tree", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": false}}
```

### d_partial

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.75, "RC_tests": 0.9615, "VC": 0.8, "details": {"agent_tests": 8, "agent_tests_fail_on_original": ["e01_reuse_daily_tally", "e03_epoch_rollover", "e07_lru_touch", "e09_slot_reuse_keys", "e13_velocity_hour_edge", "e15_entry_reuse_attempts", "e17_segment_boundaries", "e19_hold_long_ttl"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_recycle_limits": true, "M02_txid_pack": true, "M03_compact_covers": false, "M04_lru_stamp": true, "M05_idem_scope": true, "M06_hold_ids": false, "M07_ring_edge": true, "M08_entry_attempts": true, "M09_seal": true, "M10_wheel": true}, "patch_build": "ok", "ref_edge_failed": ["e05_compaction_partial_segment", "e06_compaction_partial_later", "e11_hold_wrap_untimed", "e12_hold_wrap_mixed", "e16_settlement_long"], "ref_tests_failed": ["t19_long_mixed_a"], "smoke_pass": true}}
```

### e_overaggressive

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.8, "RC_tests": 0.7308, "VC": 0.1, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e13_velocity_hour_edge"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_recycle_limits": false, "M02_txid_pack": false, "M03_compact_covers": false, "M04_lru_stamp": false, "M05_idem_scope": false, "M06_hold_ids": false, "M07_ring_edge": true, "M08_entry_attempts": false, "M09_seal": false, "M10_wheel": false}, "patch_build": "ok", "ref_edge_failed": ["e01_reuse_daily_tally", "e02_reuse_churn_tallies", "e09_slot_reuse_keys", "e10_churn_keys"], "ref_tests_failed": ["t03_overdraft_and_funds", "t06_reversal_rules", "t13_slots_reuse", "t19_long_mixed_a", "t20_long_mixed_b", "t21_long_mixed_nokeys", "t24_long_mixed_noholds"], "smoke_pass": false}}
```

### e2_overaggressive_purge

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.9, "RC_tests": 0.6923, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e09_slot_reuse_keys"], "agent_tests_fail_on_patch": ["e09_slot_reuse_keys"], "mutants_killed": {"M01_recycle_limits": false, "M02_txid_pack": false, "M03_compact_covers": false, "M04_lru_stamp": false, "M05_idem_scope": false, "M06_hold_ids": false, "M07_ring_edge": false, "M08_entry_attempts": false, "M09_seal": false, "M10_wheel": false}, "patch_build": "ok", "ref_edge_failed": ["e09_slot_reuse_keys", "e10_churn_keys"], "ref_tests_failed": ["t06_reversal_rules", "t11_idem_reopen_name", "t12_idem_eviction", "t13_slots_reuse", "t19_long_mixed_a", "t21_long_mixed_nokeys", "t23_close_rules", "t24_long_mixed_noholds"], "smoke_pass": true}}
```

### g_local_seal

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.65, "RC_tests": 0.8077, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e17_segment_boundaries"], "agent_tests_fail_on_patch": ["e17_segment_boundaries"], "mutants_killed": {"M01_recycle_limits": false, "M02_txid_pack": false, "M03_compact_covers": false, "M04_lru_stamp": false, "M05_idem_scope": false, "M06_hold_ids": false, "M07_ring_edge": false, "M08_entry_attempts": false, "M09_seal": false, "M10_wheel": false}, "patch_build": "ok", "ref_edge_failed": ["e03_epoch_rollover", "e04_epoch_keys_batches", "e05_compaction_partial_segment", "e06_compaction_partial_later", "e16_settlement_long", "e17_segment_boundaries", "e18_segment_stats_long"], "ref_tests_failed": ["t18_compaction_blocked", "t19_long_mixed_a", "t20_long_mixed_b", "t21_long_mixed_nokeys", "t24_long_mixed_noholds"], "smoke_pass": true}}
```

### h_local_txid

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.9, "RC_tests": 1.0, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e03_epoch_rollover"], "agent_tests_fail_on_patch": ["e03_epoch_rollover"], "mutants_killed": {"M01_recycle_limits": false, "M02_txid_pack": false, "M03_compact_covers": false, "M04_lru_stamp": false, "M05_idem_scope": false, "M06_hold_ids": false, "M07_ring_edge": false, "M08_entry_attempts": false, "M09_seal": false, "M10_wheel": false}, "patch_build": "ok", "ref_edge_failed": ["e03_epoch_rollover", "e04_epoch_keys_batches"], "ref_tests_failed": [], "smoke_pass": true}}
```

### i_local_scope

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 0.9615, "VC": 0.2, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e09_slot_reuse_keys"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_recycle_limits": true, "M02_txid_pack": false, "M03_compact_covers": false, "M04_lru_stamp": false, "M05_idem_scope": true, "M06_hold_ids": false, "M07_ring_edge": false, "M08_entry_attempts": false, "M09_seal": false, "M10_wheel": false}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": ["t11_idem_reopen_name"], "smoke_pass": true}}
```

