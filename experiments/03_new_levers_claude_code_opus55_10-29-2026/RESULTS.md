# Experiment 03: new difficulty levers (VSC-HX-10, VSC-HX-12), Opus 5.5 first

Date: 2026-10-29. One attempt per task, 45 minute cap, public material only; gold and hidden tests never shown. Agent: Opus 5.5, default effort, run as a subagent inside my own agent runtime (not the standalone Claude Code CLI). Open-weight model not run.

Experiment 02 showed size, module count and variant count do not raise difficulty. Experiment 03 changes the lever, not the size (spec: "Hard tier v4" in `SPEC_TASKS.md`). Each task was checked by a second reviewer (a different model): all four checks passed for both (fairness, public leaks, hidden-test scope, reproducible controls).

## Per task (one row per line)

Accepted = not saturated by Opus (criterion 4 in `ACCEPTANCE.md`).

- VSC-HX-10 (train, Python ledgerkeep ledger service, lever: long stateful runs, 1758 lines, 25 modules, K=10, 13 decoys): not accepted. Harsh 1, smooth 1.000. All 10 mutants killed, 10 own tests (all fail on the original). Opus also fixed one extra thing (max amount 1000000000 refused) that the hidden tests did not penalise. Solver time about 5 minutes.
- VSC-HX-12 (test, Python crateyard package registry, lever: no README rule, convention only in the code, 1898 lines, 31 modules, K=9, 8 decoys): not accepted. Harsh 1, smooth 1.000. All 9 mutants killed, 10 own tests. Solver time about 6 minutes.
- VSC-HX-11 (val, performance defects): not built. The authoring model was stopped by its safety filter at the step of building large timeout-inducing inputs; gold and mutants exist only as a partial draft (not in this repo). The performance lever is untested.

Accepted: 0 of 2 (provisional; human check, criterion 5, not done).

## Four metrics, same 2 tasks

- Opus 5.5: Harsh int 2/2 saturated. Smooth int 1.000. Harsh int_ref 2/2 saturated. Smooth int_ref 1.000.

Raw scores: `opus55/scores/`, agent output (patch, tests): `opus55/<task>/out/`, aggregate: `opus55/aggregate.txt`. Solver subagents could not write `REPORT.md` (tool refused); the reports in `out/REPORT.md` were saved by me from their final replies.

## Caveats

- HX-10: no README is silent on a rule, but README states the rules plainly (e.g. fresh accounts start with nothing spent). M07 (velocity window) and M10 (timer wheel) need logical time, not many commands. M02, M03, M06, M08, M09 are findable by reading one function against the README. A dead `clear_slot` method in `limits.py` points at M01. M09 makes the original exit 86 on any stream over 128 records, which reveals the lever.
- HX-10: two ref cases (`e13`, `t05`) contain compound durations the grammar rejects, so they do not test what was intended; the later lines still kill the variant.
- HX-12: M04, M06, M07 are one-function reads once the convention is noticed; M02, M05, M08 make the consistency check fire.
- Both tasks smaller than v3 (about 1.8-1.9k lines), by design of v4.
- No human check, no open-weight run, no reverse-engineering task.

## What this says

Opus 5.5 saturates all 12 tasks built so far, again in about 5-6 minutes each. Long stateful runs and conventions-only-in-code did not defeat it: it reads the whole program, reasons about each unit against the code's own patterns, and writes one test per defect. Levers still untested: performance defects (HX-11, blocked at authoring), much larger programs it cannot read in one pass, and defects that need running code (a driver that finds an interaction) rather than reading.

Technical decisions: credited cc opus 5.5 xhigh.
