# Controls (real scorer output, `python3 private/score_task.py <task> private/controls/<name>`)

Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with `sh private/build_private.sh && python3 private/run_controls.py`.

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |
|---|---|---|---|---|---|---|
| a_original | 0.0 | 0.0 | 0.0 | 0.96 | 0.0 | (a) unpatched source as patch, plus one correct test. ref_tests failed: t06_prerelease_unpublish_late; ref_edge failed: e01_disabled_user_tag_add, e02_disabled_user_tag_rm, e03_prune_refund_partial_kib, e04_prune_refund_small, e05_prerelease_not_latest, e06_first_release_prerelease, e07_fetch_bad_requirement, e08_fetch_bad_requirement_forms, e09_remove_sole_owner, e10_remove_user_mixed, e11_invite_accept_at_deadline, e12_invite_custom_ttl_boundary, e13_top_size_ties, e14_top_size_cutoff, e15_unpublish_tagged_release, e16_unpublish_prerelease_tag, e17_dependents_private_hidden, e18_dependents_anonymous; mutants killed: 0/9 |
| b_gold | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | (b) gold as patch; every ref_edge plus two ref_tests as agent tests. ref_tests failed: -; ref_edge failed: -; mutants killed: 9/9 |
| c_empty | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | (c) empty out/. ref_tests failed: -; ref_edge failed: -; mutants killed: 0/9 |
| d_partial | 1.0 | 1.0 | 0.7778 | 0.96 | 0.7778 | (d) every variant fixed except the two quietest (tag commands resolve the actor without the disabled check; publish moves latest to a higher pre-release); one test per fixed variant. ref_tests failed: t06_prerelease_unpublish_late; ref_edge failed: e01_disabled_user_tag_add, e02_disabled_user_tag_rm, e05_prerelease_not_latest, e06_first_release_prerelease; mutants killed: 7/9 |
| e_overaggressive | 1.0 | 0.0 | 0.1111 | 0.6 | 0.7222 | (e) gold plus 'hardening' of table-listed exceptions: fetch of public packages needs a role, exact pins no longer select yanked releases, pre-releases get the stable unpublish grace. ref_tests failed: t03_public_fetch_anonymous, t06_prerelease_unpublish_late, t07_yanked_exact_pin, t08_embargo_roles, t15_big_script, t18_disable_enable, t20_top_ties, t21_canonical_names, t23_deprecate_notes, t25_dependency_visibility; ref_edge failed: e05_prerelease_not_latest, e06_first_release_prerelease, e07_fetch_bad_requirement, e08_fetch_bad_requirement_forms, e16_unpublish_prerelease_tag; mutants killed: 1/9 |
| e2_overaggressive_roles | 1.0 | 1.0 | 0.1111 | 0.88 | 1.0 | (e2) gold plus 'hardening': no embargo bypass for owners/maintainers, admins lose the 'owner' action; plus loosening unyank to maintainers. ref_tests failed: t05_admin_actions, t08_embargo_roles, t10_unyank_owner_only; ref_edge failed: -; mutants killed: 1/9 |
| g_minority_invites | 1.0 | 1.0 | 0.1111 | 1.0 | 0.8889 | (g) all fixed except the invite deadline, which is harmonised the wrong way: the pending-invite listing changed to the accept path's '>' comparison. ref_tests failed: -; ref_edge failed: e11_invite_accept_at_deadline, e12_invite_custom_ttl_boundary; mutants killed: 1/9 |
| h_minority_rank | 1.0 | 0.0 | 0.1111 | 0.88 | 0.8889 | (h) all fixed except the size ranking, harmonised the wrong way: the shared rank helper changed to the size report's reverse sort. ref_tests failed: t04_private_visibility, t15_big_script, t20_top_ties; ref_edge failed: e13_top_size_ties, e14_top_size_cutoff; mutants killed: 1/9 |

## (f) Mutants against smoke and ref_edge

Each mutant is gold with exactly one defect brought back (`python3 private/check_variants.py` gives the same data plus ref_tests).

| Mutant | smoke failed | ref_edge failed |
|---|---|---|
| M01_tag_actor | none | e01_disabled_user_tag_add, e02_disabled_user_tag_rm |
| M02_prune_refund | none | e03_prune_refund_partial_kib, e04_prune_refund_small |
| M03_latest_prerelease | none | e05_prerelease_not_latest, e06_first_release_prerelease |
| M04_fetch_req_guard | none | e07_fetch_bad_requirement, e08_fetch_bad_requirement_forms |
| M05_remove_last_owner | none | e09_remove_sole_owner, e10_remove_user_mixed |
| M06_invite_deadline | none | e11_invite_accept_at_deadline, e12_invite_custom_ttl_boundary |
| M07_top_size_order | none | e13_top_size_ties, e14_top_size_cutoff |
| M08_unpublish_tags | none | e15_unpublish_tagged_release, e16_unpublish_prerelease_tag |
| M09_dependents_visibility | none | e17_dependents_private_hidden, e18_dependents_anonymous |

## Raw scorer output

### a_original

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.96, "VC": 0.0, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_disabled_user_tag_add"], "agent_tests_fail_on_patch": ["e01_disabled_user_tag_add"], "mutants_killed": {"M01_tag_actor": false, "M02_prune_refund": false, "M03_latest_prerelease": false, "M04_fetch_req_guard": false, "M05_remove_last_owner": false, "M06_invite_deadline": false, "M07_top_size_order": false, "M08_unpublish_tags": false, "M09_dependents_visibility": false}, "patch_build": "ok", "ref_edge_failed": ["e01_disabled_user_tag_add", "e02_disabled_user_tag_rm", "e03_prune_refund_partial_kib", "e04_prune_refund_small", "e05_prerelease_not_latest", "e06_first_release_prerelease", "e07_fetch_bad_requirement", "e08_fetch_bad_requirement_forms", "e09_remove_sole_owner", "e10_remove_user_mixed", "e11_invite_accept_at_deadline", "e12_invite_custom_ttl_boundary", "e13_top_size_ties", "e14_top_size_cutoff", "e15_unpublish_tagged_release", "e16_unpublish_prerelease_tag", "e17_dependents_private_hidden", "e18_dependents_anonymous"], "ref_tests_failed": ["t06_prerelease_unpublish_late"], "smoke_pass": true}}
```

### b_gold

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 1.0, "VC": 1.0, "details": {"agent_tests": 20, "agent_tests_fail_on_original": ["e01_disabled_user_tag_add", "e02_disabled_user_tag_rm", "e03_prune_refund_partial_kib", "e04_prune_refund_small", "e05_prerelease_not_latest", "e06_first_release_prerelease", "e07_fetch_bad_requirement", "e08_fetch_bad_requirement_forms", "e09_remove_sole_owner", "e10_remove_user_mixed", "e11_invite_accept_at_deadline", "e12_invite_custom_ttl_boundary", "e13_top_size_ties", "e14_top_size_cutoff", "e15_unpublish_tagged_release", "e16_unpublish_prerelease_tag", "e17_dependents_private_hidden", "e18_dependents_anonymous"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_tag_actor": true, "M02_prune_refund": true, "M03_latest_prerelease": true, "M04_fetch_req_guard": true, "M05_remove_last_owner": true, "M06_invite_deadline": true, "M07_top_size_order": true, "M08_unpublish_tags": true, "M09_dependents_visibility": true}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": true}}
```

### c_empty

```
{"IC_fix": 0.0, "IC_tests": 0.0, "RC_edge": 0.0, "RC_tests": 0.0, "VC": 0.0, "details": {"agent_tests": 0, "agent_tests_fail_on_original": [], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_tag_actor": false, "M02_prune_refund": false, "M03_latest_prerelease": false, "M04_fetch_req_guard": false, "M05_remove_last_owner": false, "M06_invite_deadline": false, "M07_top_size_order": false, "M08_unpublish_tags": false, "M09_dependents_visibility": false}, "patch_build": "missing tree", "ref_edge_failed": [], "ref_tests_failed": [], "smoke_pass": false}}
```

### d_partial

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.7778, "RC_tests": 0.96, "VC": 0.7778, "details": {"agent_tests": 7, "agent_tests_fail_on_original": ["e03_prune_refund_partial_kib", "e07_fetch_bad_requirement", "e09_remove_sole_owner", "e11_invite_accept_at_deadline", "e13_top_size_ties", "e15_unpublish_tagged_release", "e17_dependents_private_hidden"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_tag_actor": false, "M02_prune_refund": true, "M03_latest_prerelease": false, "M04_fetch_req_guard": true, "M05_remove_last_owner": true, "M06_invite_deadline": true, "M07_top_size_order": true, "M08_unpublish_tags": true, "M09_dependents_visibility": true}, "patch_build": "ok", "ref_edge_failed": ["e01_disabled_user_tag_add", "e02_disabled_user_tag_rm", "e05_prerelease_not_latest", "e06_first_release_prerelease"], "ref_tests_failed": ["t06_prerelease_unpublish_late"], "smoke_pass": true}}
```

### e_overaggressive

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.7222, "RC_tests": 0.6, "VC": 0.1111, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e01_disabled_user_tag_add"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_tag_actor": true, "M02_prune_refund": false, "M03_latest_prerelease": false, "M04_fetch_req_guard": false, "M05_remove_last_owner": false, "M06_invite_deadline": false, "M07_top_size_order": false, "M08_unpublish_tags": false, "M09_dependents_visibility": false}, "patch_build": "ok", "ref_edge_failed": ["e05_prerelease_not_latest", "e06_first_release_prerelease", "e07_fetch_bad_requirement", "e08_fetch_bad_requirement_forms", "e16_unpublish_prerelease_tag"], "ref_tests_failed": ["t03_public_fetch_anonymous", "t06_prerelease_unpublish_late", "t07_yanked_exact_pin", "t08_embargo_roles", "t15_big_script", "t18_disable_enable", "t20_top_ties", "t21_canonical_names", "t23_deprecate_notes", "t25_dependency_visibility"], "smoke_pass": false}}
```

### e2_overaggressive_roles

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 1.0, "RC_tests": 0.88, "VC": 0.1111, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e11_invite_accept_at_deadline"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_tag_actor": false, "M02_prune_refund": false, "M03_latest_prerelease": false, "M04_fetch_req_guard": false, "M05_remove_last_owner": false, "M06_invite_deadline": true, "M07_top_size_order": false, "M08_unpublish_tags": false, "M09_dependents_visibility": false}, "patch_build": "ok", "ref_edge_failed": [], "ref_tests_failed": ["t05_admin_actions", "t08_embargo_roles", "t10_unyank_owner_only"], "smoke_pass": true}}
```

### g_minority_invites

```
{"IC_fix": 1.0, "IC_tests": 1.0, "RC_edge": 0.8889, "RC_tests": 1.0, "VC": 0.1111, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e03_prune_refund_partial_kib"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_tag_actor": false, "M02_prune_refund": true, "M03_latest_prerelease": false, "M04_fetch_req_guard": false, "M05_remove_last_owner": false, "M06_invite_deadline": false, "M07_top_size_order": false, "M08_unpublish_tags": false, "M09_dependents_visibility": false}, "patch_build": "ok", "ref_edge_failed": ["e11_invite_accept_at_deadline", "e12_invite_custom_ttl_boundary"], "ref_tests_failed": [], "smoke_pass": true}}
```

### h_minority_rank

```
{"IC_fix": 0.0, "IC_tests": 1.0, "RC_edge": 0.8889, "RC_tests": 0.88, "VC": 0.1111, "details": {"agent_tests": 1, "agent_tests_fail_on_original": ["e03_prune_refund_partial_kib"], "agent_tests_fail_on_patch": [], "mutants_killed": {"M01_tag_actor": false, "M02_prune_refund": true, "M03_latest_prerelease": false, "M04_fetch_req_guard": false, "M05_remove_last_owner": false, "M06_invite_deadline": false, "M07_top_size_order": false, "M08_unpublish_tags": false, "M09_dependents_visibility": false}, "patch_build": "ok", "ref_edge_failed": ["e13_top_size_ties", "e14_top_size_cutoff"], "ref_tests_failed": ["t04_private_visibility", "t15_big_script", "t20_top_ties"], "smoke_pass": false}}
```

