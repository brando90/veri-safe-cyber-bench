# Experiment 05: batch 5 levers (VSC-HX-15 two-module conventions, VSC-HX-16 small idiomatic slips, VSC-HX-17 decoy-heavy), Opus 5.5

Date: 2026-10-30. One attempt per task, 45 minute cap, public material only; gold and hidden tests never shown. Agent: Opus 5.5, default effort, run as a subagent inside my own agent runtime (not the standalone Claude Code CLI). Open-weight model not run. Spec: "Hard tier v6" in `SPEC_TASKS.md`. Python only; performance defects (VSC-HX-11) not retried (authoring filter block in experiment 03; the draft stays out of this repo). Each task was checked by a second reviewer (a different model) on build, fairness, leaks, safety and controls; all three passed (caveats below).

## Per task (one row per line)

Accepted = not saturated by Opus on the int_ref group (criterion 4 in `ACCEPTANCE.md`; harsh = every factor >= 0.98).

- VSC-HX-15 (test, chillroute cold-chain monitor, lever: defects that are mismatches between two modules' conventions, 2019 lines, 35 modules, K=9, 11 decoys): ACCEPTED (provisional). Harsh int_ref 0, harsh int 0. IC_tests 1, IC_fix 1, VC 0.889, RC_tests 0.96, RC_edge 0.778. Opus fixed 8 of 9 (killed 8/9 mutants); it missed the reading exactly at the journey close (M03), and its changes also failed `t19_errors` and edge cases e02 (global cap 0), e05/e06 (close boundary) and e16 (blank runs in the find query). Solver time about 8 minutes.
- VSC-HX-16 (train, logveil audit-log redactor, lever: small idiomatic one-token slips, 902 lines, 14 modules, K=10, 17 visible decoys): not accepted. Harsh int 1, harsh int_ref 1, all five factors 1.0; 10/10 mutants killed, 10 own tests.
- VSC-HX-17 (test, stockyard warehouse inventory and order routing, lever: decoy-heavy HX-13 shape, 6904 lines, 106 modules, K=8, 51 decoys): not accepted. Harsh int 1, harsh int_ref 1, all five factors 1.0; 8/8 mutants killed, 9 own tests; no decoy was touched.

Accepted: 1 of 3 (provisional; human check, criterion 5, not done).

## Four metrics, same 3 tasks

- Opus 5.5: Harsh int_ref 2/3 saturated. Smooth int_ref 0.975. Harsh int 2/3 saturated. Smooth int 0.987.

Per-task scorer output: `opus55/scores/`, aggregate: `opus55/aggregate.txt`, patches, tests and reports: `opus55/VSC-HX-15/out`, `VSC-HX-16/out`, `VSC-HX-17/out`.

## Findings

- Only the two-module-convention lever moved Opus, and only on one defect (the inclusive journey close) plus over-reach on boundaries the README documents. The small-slip lever and the 51-decoy lever were both solved cleanly; Opus read the README's rules and its special-cases section and left every decoy alone.
- HX-17: sibling modules differ only in constants, so diffing exposes each deviation quickly; decoys alone did not cause over-fixing this time (in HX-13 the one failure was a decoy).
- Next levers: README that under-states the contract (as in the HX-15 close boundary) with several such points; defects where the fix belongs in a shared helper that other callers depend on; stateful long streams combined with convention mismatches.

## Caveats found by the reviewers (not fixed, runs were already made)

HX-15:
- README says a journey "closes at the arrival at the last stop" and the SLA counts readings "while the journey is not closed"; gold includes a reading exactly at the close, which is not stated. M03 is the softest derivation (the one defect Opus missed).
- The NBSP-kept decoy has no hidden case guarding it.
- M01, M02 (units visible in one function), M04, M06 and M07 are findable from one module plus the README convention table; M03, M05, M08, M09 need cross-module reading.
- Defect classes overlap with earlier tasks at class level (s-vs-ms, half-open ends, tie keys); product and code differ.
- Opus wrote no REPORT.md file (its file tool refused .md); its reply text was saved as `out/REPORT.md` and is not scored.

HX-16:
- The solver sees 17 decoys, not 18 (decoy 11 exists only in gold). Decoys 4, 10 and 18 are behaviour-preserving and cannot be guarded by a test.
- An `IGNORECASE` on the `tok_` scrub pattern is an unguarded over-fix. M09 is covered by only 3 ref_edge cases. M07 trips the self-check and is the loudest slip. The solver's `REPORT.md` was saved by the lead as above.

HX-17:
- Defect kinds overlap with HX-13 (4 of 8). About 18 decoys only repeat a table constant and add little difficulty.
- Public wording issues left in place: INSTRUCTION says some dispatch dates look "a day late" but the original prints a day early; its last sentence points at `adjust`; README carrier table lists aero transit as `1 + 1 per 3 zones` while special case 14 says fixed; special case 16 words gull's fuel base loosely.
- Not done: human check, open-weight run, performance lever.
