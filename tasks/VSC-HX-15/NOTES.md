# VSC-HX-15 author notes (private)

chillroute: toy cold-chain shipment monitor. 35 Python modules (2,019 lines of
.py, README about 130 more). Lever: "two-module-convention defects". Each
defect is a one-line disagreement between two modules; each module read alone
is idiomatic and consistent. The README documents every shared convention once,
in a table (boundary, quantity, convention, owner). The last column says which
module owns the convention (the contract); the table is in general words and
never names a defect. The public report is a symptom class only.

Internal units: instants integer ms; temperatures integer tenths; sensor range
-400..600 tenths; clock hour = ms // 3_600_000.

## Defects (K = 9, one mutant each in private/mutants)

| Mutant | Boundary (modules) | Defect | Owner (README) | Chain |
|---|---|---|---|---|
| M01_cap_zero | config/shipments -> quota | quota.admit tests `used >= limit` without the `limit and` guard: cap 0 (global, or per-shipment override) refuses every reading instead of meaning unlimited | config | config, shipments, quota (3) |
| M02_hold_units | excursions/config -> alerts | alerts compares the excursion length (whole seconds) with the hold in milliseconds and prints the limit divided back; excursion alerts never fire | excursions (seconds) | config, excursions, alerts (3) |
| M03_journey_end | windows -> sla | sla selects up to the close instant with the half-open end, so a reading exactly at the close is dropped | windows (half-open) | readings, windows, sla (3) |
| M04_stop_base | shipments -> legs, places | legs asks shipments for arrivals with 0-based numbers; shipments is 1-based as typed | shipments | places, shipments, legs (3) |
| M05_skew_sign | shipments -> ingest -> calib | ingest passes +skew to calib.correct, which adds the offset; positive skew means the logger runs ahead, so the correction must be negative | shipments / calib | shipments, ingest, calib (3) |
| M06_label_escape | export -> tsvfmt | export writes the label through row() without esc; the reader unescapes, so backslashes are lost in the cycle | tsvfmt | export, tsvfmt (2) |
| M07_tie_precision | sla -> ranking | ranking sorts on the raw ratio instead of the integer tenths shown; equal shown scores are not ordered by id | sla | sla, ranking, board (3) |
| M08_query_clean | textnorm -> search | find does not clean the query like a stored label (NFD queries and inner blank runs fail) | textnorm | textnorm, cmd_views, search (3) |
| M09_clamp_order | units/ingest -> calib | ingest clamps the raw temperature (via parse_tenths bounds) before the offset; calib clamps last | calib | units, ingest, calib (3) |

Chains of three or more: M01, M02, M03, M04, M05, M07, M08, M09 (counting the
adapter or the helper that carries the value).

Intended fixes (= private/gold): see the exact edits in make_variants.py.

## Wrong-side traps (fixing the owner or the adapter instead)

* M01: treating 0 as "unlimited" in `Shipments.effective_cap` makes `ship show` print a different text and changes override semantics (ref_tests t01, e01).
* M02: changing excursions.duration to ms changes the excursion listings and report (t04, t05).
* M03: widening windows.select to inclusive changes every range and window listing (t02, e07).
* M04: shifting the stop numbers in shipments breaks report stops and arrive (t07).
* M05: flipping the sign in calib.correct breaks `shift` (t11).
* M06: escaping inside tsvfmt.row double-escapes the site export (t23, t10).
The e2_wrong_side control repairs those six on the other side; it fails
ref_tests t01, t02, t04, t05, t07, t09, t10, t11, t17, t21, t23.

## Decoys (odd-looking but correct; all exercised by ref_tests)

1. cmd_common.user_range adds 1 ms to `to=`: user ranges are inclusive, windows is half-open (t02).
2. places.Routes.stop_at is 0-based while stops are typed 1-based (t07, t19; legs adapts with i, i+1).
3. legs uses `windows.select(rs, left, came)`: half-open is right for legs (t04 family, e07).
4. retention keeps a reading exactly at the cutoff (bisect_left) (t09).
5. site export uses erow while `tsvfmt.row` joins raw (t23).
6. Only ASCII blanks collapse in labels; NBSP is kept. REVIEW NOTE: t01/t24
   only exercise the ASCII collapsing; no hidden .in contains a non-ASCII
   blank, so the "NBSP is kept" half is UNGUARDED (the OA_STRIP_ALL edit of
   control e alone fails no hidden case; control e fails ref_tests only
   through its other four edits). To guard it, add a ref_tests case with a
   U+00A0 inside a label (e.g. in t24) and regenerate CONTROLS.md.
7. slack=0 and hmax=0 are literal values; keep, gap, spike, cap 0 mean off (t17, t22).
8. Delay in minutes truncates toward zero; averages round half up (t03, t17).
9. config durations are minutes but gap is seconds (t05).
10. legacy.py is dead code with inclusive ranges and rounded durations.
11. handoff signature uses UTF-8 bytes of the party (t16).

## Controls (see CONTROLS.md for the real scorer output)

a original, b gold, c empty, d partial (M07 and M09 left), e over-aggressive
(prune drops at cutoff, user range end exclusive, labels collapse every
whitespace char, delays floor, averages use round()), e2 wrong-side, p1 find
NFC-only; f every mutant against smoke and ref_edge.

## Rebuild

`sh private/build_private.sh && python3 private/check_variants.py && python3 private/run_controls.py`
(deterministic: fixed seeds; run_controls takes a couple of minutes). Remove
every `__pycache__` afterwards.
