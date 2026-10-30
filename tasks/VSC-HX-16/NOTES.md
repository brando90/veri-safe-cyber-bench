# VSC-HX-16 author notes: logveil, small idiomatic slips

Hypothesis under test: a strong reader finds large structural defects quickly,
but small one-token slips that read as normal Python (and several of which
change the same output) survive a skim. The product is a toy audit-log
redaction and retention tool; every slip has a defensive flavour (a value
shown that should be hidden, a record kept that should be gone, an alert that
does not fire). README documents each general rule in ordinary words; no
public file has a comment or docstring that states a rule next to a slip.

Files: `public/` (what the solver sees: INSTRUCTION.md, src/ with README.md,
build.sh and 14 modules, smoke/ with five normal sessions), `private/gold/`
(fixed tree), `private/make_variants.py` (derives public/src, the ten
mutants and the control trees from gold by exact text edits),
`private/make_inputs.py` (hand-written and seeded generated sessions),
`private/build_private.sh` (rebuild, expected outputs come from gold),
`private/check_variants.py`, `private/run_controls.py` (writes CONTROLS.md),
`private/score_task.py` (HX-14's scorer, logic unchanged).

## The ten slips (K = 10), the README rule, the fix

| Mutant | Where | Slip | README rule | Fix |
|---|---|---|---|---|
| M01 | records.parse_fields | `token.rpartition("=")` | field name is everything before the FIRST `=`; value may contain `=` | `partition` |
| M02 | names.base | `.lstrip("x-")` | a single leading `x-` is ignored | `removeprefix("x-")` |
| M03 | maskers.partial | `value[-keep:]` | visible tail is length//4; shorter than 4 is fully masked | `value[len(value) - keep:]` (a zero tail via `-0` shows the whole value) |
| M04 | scanner.scrub | `re.sub(PAIR, f, text, re.IGNORECASE)` | any letter case, every occurrence | `flags=re.IGNORECASE` (the flag lands in the count position: 2 replacements, case-sensitive) |
| M05 | policy.prefix_checks | lambda closes over loop variable | every prefix rule counts | bind with `p=prefix` |
| M06 | store.World.limit_for | `limits.get(source) or default` | limit 0 alerts on any record | `get(source, default)` |
| M07 | store.Store.purge | `self.records.remove()` inside the loop over it | purge removes every record older than the limit | build a new list |
| M08 | policy.Policy.temporary | `copy.copy(self)` then `keep |= ...` | `export ... keep=` is for that export only | `copy.deepcopy` (or a non in-place union) |
| M09 | reports.share | `"%.1f" % (100.0 * part / whole)` | share has one decimal, halves rounded up | integer half-up arithmetic (1/16 is 6.25 exactly and prints 6.2) |
| M10 | reports.ranked | sort `(count, name)` tuples with `reverse=True` | highest count first, equal counts in name order | key `(-count, name)` |

Interactions (fixing one changes what another looks like): M01 + M02 + M05
decide whether a field is recognised at all (a padded or `x-` field with a
second `=` is silently left alone, then a second prefix rule is silently
ignored); M03 + M04 meet in message scrubbing (the first two occurrences are
masked, a short value in them is shown whole, so fixing M04 alone exposes
M03); M09 + M10 both show in the same report lines; M06 changes which sources
appear in the alert and `at limit` lines that M09 and M10 do not touch; M07 is
visible only through the self-check (exit 86) or the next report.

## Decoys (correct code that looks like a slip; guarded by a ref_test where a "fix" changes behaviour)

(Second review, 2026-10-30: decoys whose natural "fix" is behaviour-preserving
(4, 10, 18) cannot be and need not be guarded; 11 is not in `public/` at all,
see its entry; 15 and 17 guards were verified and added below.)

1. stamp.older_than: `>` (exactly the limit old is kept) - t10.
2. windows.peak: `>=` in the shrink loop (a record exactly one window old is outside) - t12.
3. windows.alerts `>` versus at_limit `==` (equal to the limit is `at limit`, not an alert) - t12.
4. maskers.pseudo: mutable default `_memo` (a cache keyed by salt and value, never wrong) - t02 (removing the memo is behaviour-preserving: no hidden test changes; time sink only).
5. records.domain_of: `rpartition("@")` (domain after the LAST @) - t17.
6. names.clean_id: `lstrip("#")` (any number of leading `#`) - t18.
7. records.parse_size: `fields.get("bytes") or "0"` (an empty value is 0) - t08, t21.
8. stamp.days_ahead: `-(-ahead // DAY)` (rounded up) - t13.
9. reports.build: `round(total / n)` (documented half-to-even) - t14.
10. redact.apply: `copy.copy(record)` plus `dict(record.fields)` (flat str values, no aliasing). Changing it to `deepcopy` is behaviour-preserving: no hidden test changes (verified); no guard possible, time sink only.
11. NOT A PUBLIC DECOY: the `p=prefix` default argument exists only in `private/gold/policy.py` (it is the M05 fix); `public/src` has the late-binding lambda. Do not count it (17 decoys visible to the solver, still >= 8).
12. reports.level_rank: `except ValueError` around `index` (unknown levels sort last) - t16.
13. redact.shorten: `[:77] + "..."` after a length test of 80 - t07.
14. reports.build: `max(records, key=size)` returns the lowest id on equal sizes - t21.
15. reports.field_stats: `table(...)[1:]` drops the empty title row - t19, t20 (and smoke s2) fail if the slice is removed (verified).
16. stamp.parse: the offset sign (local time minus offset) - t09.
17. scanner._mask_pair slicing of the matched head - t06 (and smoke s4, t25-t27) fail if the head is sliced with an absolute index `[: m.start(1)]` (verified); an equivalent rewrite such as `[: -len(m.group(1))]` changes nothing, which is fine.
18. `is None` on the documented "no action" return value of Policy.action_for. `not action` / `== None` is behaviour-preserving (actions are non-empty strings): no hidden test changes (verified); time sink only.

Traps / over-aggressive fixes caught by ref_tests (controls e, e2, e3, e4):
changing a boundary comparison (1, 2, 3), average half-up (9), `removeprefix`
for ids (6), rejecting an empty bytes value (7), rounding days ahead down (8),
domain after the first @ (5), masking all values under 8 characters (README
says 4), stripping `x-` anywhere in a name, purging records dated after the
clock, alphabetical level order, reverse id order in purge output.
Partial fix: control d leaves M08 and M09 (the two quietest) and scores
RC_edge below 1 and VC 0.8.

## Shape of the hidden tests

smoke: five ordinary sessions (tables without ties, no `=` inside values, no
x-names starting with a second x, one prefix rule). ref_tests: 27 sessions
that the original also passes (behaviour, decoys, error texts; three are
seeded random sessions accepted only if gold, original and every mutant
agree). ref_edge: 27 sessions that all fail on the original; one or more per
slip plus four interaction sessions and three seeded random sessions with
hazard shapes. Every mutant fails at least two ref_edge cases and no smoke
case (CONTROLS.md, section f).
