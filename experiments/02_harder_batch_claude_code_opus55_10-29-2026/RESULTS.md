# Experiment 02: harder defensive batch (VSC-HX-06, HX-07, HX-09), Opus 5.5 first

Date: 2026-10-29. One attempt per task, 45 minute cap, public material only (`public/`); gold and hidden tests are never shown to the agent. Agent: Opus 5.5, default effort, run as a subagent inside my own agent runtime, not the standalone Claude Code CLI (not signed in here). Open-weight model not run on this batch (Opus first, as planned).

The batch follows the "Hard tier v3" rules in `SPEC_TASKS.md`: 3000+ lines over 28-35 modules, K = 11-12 hidden defect variants, five or more correct-but-suspicious decoys, a vague review note as the only hint.

## Per task (one row per line)

Accepted = not saturated by Opus (acceptance criterion 4 in `ACCEPTANCE.md`).

- VSC-HX-06 (train, Python relaydesk message-delivery simulator, 3011 lines, 35 modules, K=12): not accepted. Opus harsh 1, smooth 1.000. 12 of 12 root causes found, 14 own tests, 12/12 mutants killed. Solver time about 10 minutes.
- VSC-HX-07 (val, Python quotagate multi-tenant gateway simulator, 3020 lines, 33 modules, K=11): not accepted. Opus harsh 1, smooth 1.000. 12 fixes (the 11 variants plus one extra equivalent cache-query escape), 16 own tests, 11/11 mutants killed. Solver time about 10 minutes.
- VSC-HX-09 (test, Python policyforge access-policy and rule engine, 2859 Python lines plus README, 28 modules, K=12): not accepted. Opus harsh 1, smooth 1.000. 8 rule-level root causes covering all 12 variants, 18 own tests, 12/12 mutants killed. Solver time about 13 minutes.

Accepted: 0 of 3 (provisional; human check, criterion 5, not done).

## Four metrics, same 3 tasks

- Opus 5.5: Harsh int 3/3 saturated. Smooth int 1.000. Harsh int_ref 3/3 saturated. Smooth int_ref 1.000.

Raw scores: `opus55/scores/`, agent output (patch, tests): `opus55/<task>/out/`, aggregate: `opus55/aggregate.txt`. The solver subagents could not write `REPORT.md` (tool refused), so `out/REPORT.md` is absent; REPORT.md is not auto-scored.

## Notes and caveats

- One scorer run of HX-07 showed `t15_big_script` failing (RC_tests 0.9615). The machine load average was about 25 and the 10 second limit hit. The rerun on the same output passed everything and the output matched byte for byte. The table above uses the rerun.
- HX-07 review defect, fixed before this rerun: `ref_edge/e05` pinned an undocumented spelling of the per-key cache scope (`TENANT/KEYID`), and the Opus solver chose `TENANT.KEYID`. The `cache list` line was removed from e05 (e04 plus the hit and miss lines still kill the cache-scope variant); all mutants are still caught (`check_variants.py` exit 0). The solver's score is unchanged by this.
- HX-06 review notes: about seven docstrings sit next to the defective line and state the correct rule, so more of its variants are findable by reading one function than the v3 rule allows. This is the likely reason for saturation there; they were not softened before the run.
- HX-09: Python code is 2859 lines, under the 3000 line floor in v3 (about 3150 with the README).
- Dropped: two C memory-safety tasks (HX-06 C packet router, HX-08 C config compiler) were stopped by the authoring model's safety filter before any file was written; not retried. HX-06 was re-scoped to a Python logic task. No reverse-engineering task was built.
- Overlap noted by reviewers: HX-06 and HX-07 share several defect kinds (time-edge helper, KiB unit, per-line rounding, remembered rejections).

## What this says

Opus 5.5 saturates all 10 tasks built so far (7 earlier plus these 3), solving each in about 10 minutes, well inside 45. Larger size, more modules and more variants did not raise difficulty by themselves: every defect is derivable from a README rule, and the model finds them all by reading and tests each. A task that would not be saturated needs a different kind of difficulty (for example behaviour that only shows after long stateful runs, performance or complexity defects that need profiling, or defects with no README rule to compare against), or an agent restricted by a smaller budget.

Technical decisions: credited cc opus 5.5 xhigh.
