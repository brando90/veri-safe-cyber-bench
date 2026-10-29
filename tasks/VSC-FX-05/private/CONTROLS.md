# Controls (real scorer output, `python3 score_task.py <task> private/controls/<name>`)

Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge.

| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |
|---|---|---|---|---|---|---|
| (a) gold as patch, ref_edge as agent tests | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 13 tests, all 3 mutants killed |
| (b) empty out/ | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | patch missing |
| (c) unpatched source as patch + test e01 | 0.0 | 0.0 | 0.6667 | 1.0 | 0.0769 | test fails on its own patch |
| (d) partial fix (bound params for add/find/report/discount, LIKE not literal; rename and CSV untouched) | 0.0 | 0.0 | 0.6667 | 1.0 | 0.2308 | rename/CSV variants left |
| (e) over-aggressive (rejects quotes/commas/semicolons in names, escapes numeric columns) | 1.0 | 0.0 | 0.3333 | 0.8 | 0.1538 | t11, t12, t15 broken; smoke fails |

Mutant check against hidden cases (each fails at least one):
* M1_find: e01, e02, e03, e05
* M2_rename: e05, e06, e07, e13
* M3_csv: e01, e05, e07, e08, e09, e10, e11, e13

Original fails 12 of 13 ref_edge cases and none of the 15 ref_tests.
