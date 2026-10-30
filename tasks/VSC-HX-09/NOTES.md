# VSC-HX-09 author notes (private)

policyforge: toy access-policy engine. 25 Python modules (about 2,900 lines)
plus a 330-line README that is the specification. Driven by stdin command
lines; every command's output is buffered, the consistency check
(invariant.py) runs after each command and exits 86 on a violation (secret
value in any encoding in the command's output, override rule in a standard
set, duplicate rule ids, broken parent chain, approval used or extended at or
after its deadline, approval approved by its own subject, per-set log out of
order). Synthetic and defensive: all test data is ordinary policy data.

The README states eight general rules (one matching rule; limits hold on
every path; half-open time windows; recording order; exact half-up
percentages; data is data / escape exactly once; secrets stay secret, redact
before escaping; imports checked like local changes). Every defect breaks
one of them; none is listed case by case.

## The defects (K = 12, one mutant each in private/mutants)

| Mutant | Where | Defect | README rule | Difficulty / kind |
|---|---|---|---|---|
| M01_parse_list_depth | parser.Parser._list | list literals do not call `_enter()`, so `[[[...]]]` (or parentheses mixed with lists) is not bounded by the nesting limit 32 | limits on every path; nesting counts parentheses, not, lists and calls | easy, one function |
| M02_macro_budget | evaluator._macro | a named condition is evaluated with `evaluate(ast, ctx)`, which creates a fresh 500-step budget, instead of `_eval(ast, ctx, budget)`; steps inside @name calls are not charged to the request | one budget per request, steps of named conditions count | medium, needs evaluate()'s default + budget.py + decide.py |
| M03_extend_expired | approvals.extend | uses `_require_state` (state only) instead of `_require_live`; an approval past its deadline is still extended as long as nothing refreshed it since (any check or `approve list` in between hides the defect) | half-open windows "whether or not anything has looked at it" | medium: state carried between calls; decoy `revoke` uses `_require_state` correctly |
| M04_expiry_boundary | clock.expired (shared helper) | `now > deadline` instead of `now >= deadline`: grant, extend and the use by a check all accept the deadline second | half-open windows | shared helper; the obvious local patch at the check path leaves grant/extend wrong (control g2) |
| M05_report_pct | render._summary | `"%.1f" % (100.0*a/n)` (binary float, half-even) instead of numfmt.pct1 (exact, half up); stats/whatif use pct1 | exact half-up percentages | easy-medium, convention differs between modules (1/16 -> 6.2 vs 6.3) |
| M06_approval_match | approvals._covers | fnmatch instead of patterns.match_*: `*` crosses `/`, `/a/**` does not select `/a` | one matching rule | medium, cross-module (approvals, patterns, decide) |
| M07_pattern_prefix | patterns.match_resource fast path (shared helper) | `value.startswith(base)` instead of `value == base or value.startswith(base + "/")`: `/docs/team/**` selects `/docs/teamwork/x` | one matching rule (README gives the `/docsx` example) | shared helper; local fix in decide.candidates leaves log filter, glob(), any_glob(), approvals wrong (control g1) |
| M08_log_order | decisionlog._order_key | heapq.merge of the per-set buckets keyed on time only; entries of different sets with equal time come out grouped by set name instead of by seq | recording order also for equal times | hard: ordering stability, per-set storage, only visible across sets at one time |
| M09_note_redaction | decide._condition | the condition-error note (shown on DECISION lines, in the log and reports) is not redacted; evaluator error messages quote values, including secret values | secrets in error messages and notes | medium: main.py redacts ERROR lines, decide redacts the budget note, so it looks done |
| M10_html_redact_order | render._html_report | the html layout redacts the finished escaped row instead of the plain field values; a secret containing `& < > " '` survives in its escaped form | redact a plain value before escaping; no encoding of a secret in output | medium-hard: text layout legitimately redacts the finished line (comment says why) |
| M11_bundle_mode | bundle.import_lines | validates bundle rules against the `mode=` declared on the bundle's set line instead of the target set's mode, so an override rule lands in a standard set (exit 86) | imports checked like local changes; nothing in a bundle changes the target | medium: one line, but needs the rule; checksum must be recomputed for a test |
| M12_context_escape | render._context / _html_cell | for html the context is pre-escaped when the fields are built and the builtin cell skips escaping it; the template path escapes again (double escaping), and redaction then runs on escaped text | escape exactly once where placed | hard: builtin html output is correct; only templates over html show it |

Single-function variants: M01, M03 (if the state machine is known), M05.
Cross-module (3+): M02, M06, M07, M09, M10, M11, M12. Time / ordering /
state / number convention: M03, M04, M05, M08. Shared helper must change:
M04, M07.

## Intended fix (= private/gold)

See the edits in make_variants.py (each defect is the gold text replaced by
the defective text). In short: `_enter/_leave` around list items; `_eval`
with the caller's budget; `_require_live` in extend; `now >= deadline`;
`numfmt.pct1`; patterns.match_action / match_resource in approvals;
`value == base or value.startswith(base + "/")`; merge key `(time, seq)`;
`redact.scrub` on the note; `scrub_all` before escaping in html; `mode =
target.mode`; raw context, escaped once in `_html_cell` / template.

## Decoys (look suspicious, correct because of an invariant elsewhere)

1. decide: override beats deny and approvals beat deny: documented
   precedence (control e1 flips it, fails t01/t09).
2. decide: a condition that errors makes a deny rule apply but not an allow
   rule (fail closed): documented (t02).
3. evaluator: no recursion limit: the parser bounds expression nesting and
   Budget.enter_macro bounds @name nesting (8); macros cannot be redefined so
   there are no cycles (t06).
4. budget.charge: `used > limit` lets exactly 500 steps pass: documented
   ("budget of 500 steps"); control e3 (`>=`) fails t07.
5. approvals.revoke uses `_require_state` without the live check: revoke is
   documented to work on expired approvals; control e2 fails t08.
6. render.text_line redacts the finished line: text has no escaping, so the
   line equals the plain values (contrast with M10).
7. escape.json_inner leaves non-ASCII and `/` alone; csv leaves `'` and `;`
   unquoted: documented; control e4 fails t10/t11.
8. bundle: rule ids in the bundle are parsed and ignored (rules are
   renumbered); checksum is a plain hash (documented as damage detection).
9. numfmt.pct1 / avg_int have no zero guard: every caller checks total > 0.
10. legacy.py (fnmatch matcher, v0 bundle reader without checksum, float
    percentages): dead code, not imported anywhere.
11. lint.covers_resource is a separate pattern-vs-pattern algorithm: it
    compares two patterns, not a pattern and a value.

## Traps (each caught by a hidden case; see CONTROLS.md)

* Fix only what ends in exit 86 or an obvious wrong line: control d2.
* Fix the /** prefix only at the rule-matching call site: control g1 (e14,
  e15 fail).
* Fix the deadline only where a check uses an approval: control g2 (e08,
  e09 fail).
* Write the extend test with an `approve list` (or any check) before the
  extend: the M03 mutant is not caught (the list refreshes the state).
* Notice the double escaping and "fix" it by removing escaping in
  template.render: breaks every other templated field (t13, t14).
* Harden decoys: controls e1-e4.
* Ref_tests that are easy to break: t23 (300 rules, 250 checks), t07 (budget
  exactly 500), t10/t11/t12 (exact escaping), t16 (retention + ordering),
  t22 (redaction everywhere, longest secret first).

## Regenerating

`sh private/build_private.sh` (variants, inputs, expected outputs from gold)
then `python3 private/run_controls.py` (writes CONTROLS.md, runs
check_variants.py).
