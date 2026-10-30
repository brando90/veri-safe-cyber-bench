# VSC-HX-14 author notes (private)

eventlane: toy calendar and recurrence engine. 29 Python modules (1,941 lines
of .py; the README adds about 130). Lever: "defects needing a driver to
find". Each defect shows only on a rare input shape or value combination;
hand-checkable input and the smoke cases never reach one. The README states
ten round-trip, idempotence and ordering properties and the program's
self-check (`invariant.full_check` after every command; exit 86, `INVARIANT:`
on stderr) enforces them, so a random or targeted driver has an oracle. The
public report only says that some runs fail the self-check. No comment,
docstring or README line sits next to a defect or points at one (the README
properties are general; none names a value, shape or module).

Wiring: `world.World` dispatches to evcmds (event commands), agenda, busy,
shifts, tools (helpers), exporter (text and pack export/import), stats. Data
layers: civil (day numbers), timeparse (dates, starts, snap), offsets,
durations, fields (escaping, categories, titles), varint, checksum, pack,
textrec, ids (base-32 references), names (natural id order), rules, expand
(series), events (model and store), invariant (self-check). legacy.py is dead
code (never imported).

## The defects (K = 10, one mutant each in private/mutants)

| Mutant | Module | Defect (rare shape) | README property that exposes it | How it shows |
|---|---|---|---|---|
| M01_civil_cycle_end | civil | `civil_from_days` drops the `doe // 146096` term of the era arithmetic: day numbers at the very end of a 400-year cycle (29 Feb of years divisible by 400: 1600, 2000, 2400 ...) convert to the wrong date | 1 (day to date and back) | INVARIANT on any event whose start, or an occurrence, is on such a day; also `date N` output |
| M02_category_backslash | fields | `esc_item` stops doubling a backslash in a category | 3 (escaping lossless) | INVARIANT when a category contains a backslash (text/pack record or `event cat`) |
| M03_varint_boundary | varint | continuation test `n > 0x80` instead of `>=`: the value 128 (and 16384, 2097152 ...) is written as one byte | 6 (packed record decodes to the event) | INVARIANT for an event with a field equal to 128 at a byte boundary: minute-of-day 128 (02:08), tz +01:04, seq 128, duration 128 s, 16384 s, 24d7h, skip gap 128 days, some day numbers (1992-06-06..1992-08-08 starts) |
| M04_offset_sign | offsets | the sign of `format` comes from the hour part, so offsets -00:01..-00:59 print as `+` | 2 (offset text reads back) | INVARIANT on `tz=-00:30` etc. and `offset -00:45` output |
| M05_weekly_anchor | expand | weekly series count weeks from the start date instead of the week start, so with `every>1` and a selected weekday earlier in the week than the start's weekday the series leaves the selected weeks | 7 (weekly series stays in selected weeks) | INVARIANT for `weekly;every=2;on=MO` started midweek |
| M06_snap_carry | timeparse | the `23:59:30+` rounding carry sets the hour to 0 but does not advance the day | 5 (start within 30 s of what was given) | INVARIANT for a start at 23:59:30..23:59:59 with seconds |
| M07_natural_ids | names | `natural_key` looks only at the first two chunks of an id | 10 (agenda tie order by natural id) | INVARIANT when two same-time, same-priority events have ids that tie on two chunks and differ later (`ev-1d10` vs `ev-1d9`) |
| M08_ref_width | ids | `encode` uses a float-log digit count, which is one too many for the largest sequence numbers (2^50-1 and a couple below) | 9 (reference has no leading zeros and reads back) | INVARIANT after `idseq` to the maximum and one more event |
| M09_move_skips | events | `reschedule` prunes skips before the new start is stored, so stale skips survive an `event move` | 8 (skips name occurrences) and the README sentence on move/rule | INVARIANT after skip + move of a recurring event to another weekday/day |
| M10_title_blanks | fields | `normalize_title` collapses only pairs of blanks (tab to blank, then "  " to " " once), so runs of three or more stay | 4 (title normalisation idempotent) | INVARIANT for a title with 3+ consecutive blanks |

Intended fixes (= private/gold): M01 restore the term; M02 escape the
backslash first; M03 `>=`; M04 sign from the minutes, not the hour; M05 anchor
the week at `civil.week_start(start)`; M06 carry the day; M07 compare all
chunks; M08 exact integer digit count; M09 set the start (and rule) before
pruning; M10 `re.sub(r"[ \t]+", " ", ...)`.

## Decoys (odd-looking but correct; each is exercised by a ref_tests case)

1. civil.days_in_month uses a month-length bit trick, weekday is `(z+3)%7` (t06, t13).
2. varint zigzag uses `n >> 63`; checksum is Fletcher mod 255 (t16).
3. offsets accept `Z`, `+HHMM`, `+HH`, `-00:00` (t13).
4. ids.decode accepts I, L (as 1) and O (as 0), lower case (t17).
5. All-day events are floating: the offset is stored and never applied (t20).
6. A non-breaking space is not a blank for titles and is kept (t14).
7. A yearly 29 Feb event falls on 28 Feb in other years (t06).
8. `count` includes skipped dates (t07).
9. snap rounds half up (t21); duration decimals round half up (t12).
10. legacy.py is dead code with its own (different) helpers.

## Traps (each caught by hidden cases; controls in private/CONTROLS.md)

1. Over-fixing titles with `" ".join(text.split())` (collapses NBSP): t14. Control e.
2. Printing `Z` for offset 0 (README: written `+HH:MM`): t13. Control e.
3. Moving a yearly 29 Feb to 1 March instead of 28 Feb: t06. Control e.
4. Busy merging only strictly overlapping spans (README: touching spans merge): t10. Control e2.
5. Keeping the last stale skip when pruning (instead of dropping all stale ones): t18, t19, e17, e18. Control e2.
6. Disabling the self-check: every ref_edge case also prints visible output (show, expand, export, list), so the wrong value still differs from the .out. Control g.
7. Fixing M09 by pruning at every command, or M05 by changing the series definition: the hidden sessions e22 and t19 would differ.

## Rarity measurement (private/random_driver.py, seed 7, in-process)

Sessions = independent command sequences, run from a fresh world, count to
the first INVARIANT or traceback. Cap 2,000 sessions for the ordinary driver.
"ordinary" is an independent README-driven generator (40 commands per
session; uniform dates 2000-2030, any minute of the day, offsets that are
multiples of 15 minutes from -12:00 to +14:00, plain titles with single
blanks, categories from a word list, random rules, ids from a small pool,
skips and moves on random dates). "targeted" is make_inputs.Gen with only the
hazard of that defect (150 commands per session, hazard rate 0.25).

| Tree | ordinary: sessions to first failure | targeted: sessions to first failure |
|---|---|---|
| gold | none in 2000 sessions (80,000 commands) | none in 200 sessions (30,200 commands) |
| M01_civil_cycle_end | none in 2000 sessions (80,000 commands) | 1 (151 commands) |
| M02_category_backslash | none in 2000 sessions | 1 (151 commands) |
| M03_varint_boundary | 12 sessions (480 commands) | 1 (151 commands) |
| M04_offset_sign | 2 sessions (80 commands) | 1 (151 commands) |
| M05_weekly_anchor | 4 sessions (160 commands) | 1 (151 commands) |
| M06_snap_carry | 187 sessions (7,480 commands) | 1 (151 commands) |
| M07_natural_ids | none in 2000 sessions | 1 (151 commands) |
| M08_ref_width | none in 2000 sessions | 1 (154 commands) |
| M09_move_skips | 29 sessions (1,160 commands) | 1 (151 commands) |
| M10_title_blanks | none in 2000 sessions | 1 (151 commands) |

Reading: with the self-check as oracle, a plain README-driven fuzzer finds 5
of 10 within 190 sessions (M03, M04, M05, M06, M09). The other five need a
value or shape the plain generator never draws (M01 leap day on a 400-year
boundary, M02 backslash in a category, M07 ids that tie on two chunks, M08 a
sequence number near 2^50, M10 runs of 3+ blanks). The ordinary driver
is therefore a real lever for about half of the set and M04 and M05 are
easier than intended (a 15-minute offset grid hits -00:15..-00:45 and
`every>1` weekly rules with an earlier `on` weekday are common). A driver
that widens its value grid (years across 1600..2400, whole-range
`idseq`, long blank runs, backslashes, similar ids) finds the rest quickly.
Gold never fails under either generator.

## Fairness check

Every expected output is what the README properties and rules give: gold
(private/gold) is the reference, with the README as the written contract
(properties 1-10, the move/rule skip sentence, "spans that touch are merged",
"29 February becomes 28 February", "count counts every date including
skipped ones", offsets written `+HH:MM`). Each defect is a violation of a
numbered property or a stated rule; none depends on an unwritten
convention.

## Files

* private/make_variants.py: exact-text edits of gold (asserts each target text occurs once). Writes public/src (gold plus all ten defects), private/mutants, private/controls/*/patch.
* private/make_inputs.py: writes public/smoke (5), ref_tests (28, 24 hand-written plus 4 generated hazard-free sessions), ref_edge (22: e01-e19 hand-written, two per defect except M10 which has one plus session cases; e20-e22 generated hazard sessions). All .in files are well under 1 MB.
* private/build_private.sh: rebuilds everything and regenerates every .out from gold.
* private/check_variants.py (original and mutants against smoke, ref_tests, ref_edge), run_controls.py (controls a-g and mutant table, writes CONTROLS.md), random_driver.py (rarity), score_task.py (scorer, from HX-12).

## Check results (check_variants.py)

Gold passes everything. The original passes all smoke and ref_tests and
fails all 22 ref_edge cases. Every mutant passes smoke and ref_tests and
fails at least two ref_edge cases (see CONTROLS.md section f).

Controls (CONTROLS.md): a_original RC_edge 0.0; b_gold all 1.0; c_empty all 0.0; d_partial RC_edge 0.7273 and VC 0.8; e_overaggressive RC_tests 0.4643; e2_overaggressive_listings RC_tests 0.7857; g_check_disabled RC_edge 0.0.
