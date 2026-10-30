# Experiment 04: untested levers (VSC-HX-13 too large to read in one pass, VSC-HX-14 defects needing a driver), Opus 5.5 first

Date: 2026-10-29. One attempt per task, 45 minute cap, public material only; gold and hidden tests never shown. Agent: Opus 5.5, default effort, run as a subagent inside my own agent runtime (not the standalone Claude Code CLI). Open-weight model not run.

Levers not yet tried after experiments 01-03 (spec: "Hard tier v5" in `SPEC_TASKS.md`). Performance defects (VSC-HX-11) were not retried: the authoring filter blocked them in experiment 03 and the draft stays out of this repo. Each task was checked by a second reviewer (a different model): fairness, public leaks, safety and controls passed for both (caveats below).

## Per task (one row per line)

Accepted = not saturated by Opus on the int_ref group (criterion 4 in `ACCEPTANCE.md`, harsh = every factor >= 0.98).

- VSC-HX-13 (val, Python billmill invoicing engine, lever: too large to read in one pass, 7177 lines, 109 modules, K=12, symptom-only report naming 3 of 12): ACCEPTED (provisional). Harsh int 1, harsh int_ref 0, smooth int 1.000, smooth int_ref 0.985. Opus found and fixed all 12 defects (12/12 mutants killed, 15 own tests, IC_tests 1, IC_fix 1, VC 1.0) but also changed the NY/WA split-rate tax rounding, a deliberate decoy: RC_tests 0.962 (t26_big_script), RC_edge 0.963 (e26_sweep_regions). Solver time about 8 minutes.
- VSC-HX-14 (train, Python eventlane calendar/recurrence engine, lever: defects needing a driver, 1941 lines, 29 modules, K=10): not accepted. Harsh int 1, harsh int_ref 1, smooth 1.000 on every factor. 10/10 mutants killed, 12 own tests (all fail on the original). Solver time about 6 minutes.
- VSC-HX-11 (performance defects): not retried, lever still untested.

Accepted: 1 of 2 (provisional; human check, criterion 5, not done).

## Four metrics, same 2 tasks

- Opus 5.5: Harsh int 2/2 saturated. Smooth int 1.000. Harsh int_ref 1/2 saturated (HX-14). Smooth int_ref 0.992.

Per-task scorer output: `opus55/scores/`, aggregate: `opus55/aggregate.txt`, Opus's patches, tests and reports: `opus55/VSC-HX-13/out`, `opus55/VSC-HX-14/out`.

## Findings

- Size alone still does not saturate-break Opus: a 7k-line, 109-module program was fully diagnosed in minutes. The one non-saturated factor group is the reference tests, and it moved only because Opus over-reached on a decoy, not because it missed a defect.
- The reviewer notes that in HX-13 per-service/per-region modules differ only in constants, so diffing siblings isolates 8 of 12 defects; the four singleton modules are the harder part (Opus still found them).
- HX-14 is readable more than driver-requiring: the reviewer judged about 8 of 10 defects spottable by reading in under a minute (M01 leap-cycle term and M08 float-log width need a driver or numeric care). The self-check fires on every mutant. Harder next levers would be defects whose local code is idiomatic and wrong only through two modules' conventions.

## Caveats found by the reviewers (not fixed, runs were already made)

- HX-14: `tools.parse_int` caps numbers at 12 digits, undocumented; hidden cases e15 (lines 1-4) and t17 (line 9) rely on it. A README sentence or dropping those lines would remove the risk.
- HX-14: `t28_long_ordinary` takes 2-3.5 s on gold on a loaded host; do not score in parallel. NOTES trap 7 is wrong (pruning stale skips in the check does not break e22/t19).
- HX-13: ref_tests has no plan-change case (any plan change triggers defect 9; covered by ref_edge only).
- Not done: human check, open-weight run, performance lever.
