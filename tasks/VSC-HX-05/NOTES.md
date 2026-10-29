# VSC-HX-05 author notes (private)

slotbook: toy one-chair appointment and billing back office. 17 Python
modules (about 1,900 lines) plus a 300-line README that is the specification.
Users have one role; roles inherit; permissions belong to operations; every
command runs in a savepoint; the consistency check (invariant.py, exit 86)
verifies schema, declared row-count changes, that every changed table is
writable by the actor (resolved freshly, bypassing the role cache), and that
new audit rows parse with the documented fields.

## The defects (K = 8, one mutant each in private/mutants)

All wording is plain maintenance language; all test data is ordinary text.

| Mutant | Where | Defect | General README rule it breaks | Difficulty |
|---|---|---|---|---|
| M1_import_header | transfer.check_header | header names are not checked against the documented column list; for services/appointments the names flow through `convert()` into `store.insert_record`, i.e. into SQL column names; for customers/payments extra columns are silently ignored | "Data is data" (never table/column names) + Import header rule | medium: two different symptoms (ERROR db vs silent accept) |
| M2_audit_export | audit.cmd_export | builds TSV with a plain `"\t".join`, not `formats.emit_table`; backslashes that the audit-detail escaping put in, and any TAB, are not TSV-escaped | TSV rule applies to every field "whichever command writes it" | medium: needs to notice audit details always contain escape backslashes when values have quotes |
| M3_audit_bulk | transfer `_detail` | import's batch audit writer formats `key="value"` itself without the audit escaping (normal commands use `formats.audit_detail`) | audit detail escaping; imports write "the same audit row" | medium (exit 86 on quotes/backslashes/TAB in imported text) |
| M4_status_cancel | appointments.change_status | `appt-status APPT cancelled` cancels with only appt.write; `cancel` checks appt.cancel in the command table and `customer-archive` checks it explicitly | "permissions belong to operations ... whichever command performs it" | easy-medium |
| M5_import_perm | transfer.cmd_import | import checks only import.run; the per-KIND create permission (KIND_PERMS[...][1]) is never required. billing holds import.run but not customer.write/appt.write/service.write | same operations rule; "each row creates one record exactly as the corresponding command would" | easy once import is read; exit 86 on the original |
| M6_role_deny | roles.effective | resolution is recursive: a role's own denies are removed from (own grants + parents' resolved sets); a deny on an ancestor is lost when another parent or the role itself grants the permission | "a deny anywhere in the chain wins" | hard (needs the rule, not a pattern; looks like textbook inheritance) |
| M7_role_cache | roles.invalidate | role-grant/deny drop only the changed role's cached set; cached sets of descendant roles stay stale (the consistency check bypasses the cache, so a stale grant that leads to a change ends in exit 86) | "takes effect immediately, for that role and for every role that inherits from it" | hard (cache only stale for roles resolved before the change) |
| M8_tax_report | reports.tax_summary | tax per rate recomputed as rate of the summed net (one rounding) instead of summing the stored per-line tax | "every total, subtotal and report figure is the sum of the rounded per-line amounts" | medium-hard (invoice code is correct; revenue report is correct) |

## Intended fix (= private/gold)

* check_header rejects any column not in `kind.columns` (`ERROR import: unknown column C`).
* audit-export uses `formats.emit_table(sess, "tsv", ...)`.
* import uses `formats.audit_detail(pairs)`.
* `change_status` requires appt.cancel when the new status is cancelled (after argument validation, before any change).
* `cmd_import` requires `KIND_PERMS[kind][1]` after KIND validation; a refusal prints exactly `ERROR denied: PERM`.
* `effective` collects grants and denies over the role and all ancestors, result = grants - denies.
* `invalidate` clears the whole cache (or the role and all its descendants).
* `tax_summary` sums `tax_cents` of the lines.

## Traps (each caught by a hidden case; see CONTROLS.md)

1. Partial fix of the visible exit-86 symptoms only (M3, M5, M4): control (d), RC_edge 0.35.
2. Fixing M1 only where it produces `ERROR db:` (services) misses the silent customers case: e02.
3. Fixing M5 only for customers: e11 (appointments, services by billing), e12 (custom role with import.run + customer.write: services and payments refused).
4. Fixing M4 by listing appt.cancel for `appt-status` in the command table: frontdesk can no longer mark done/noshow (t03, t12 and nearly everything after BOOK): control (e), RC_tests 0.31.
5. Requiring all write permissions for every import: billing payment imports break (t08, t16): control (e2), RC_tests 0.875.
6. "Fixing" money by switching to Python `round()`: half-cent lines change (t05, t06, t13...): control (e3), RC_tests 0.69.
7. Refusing quotes/backslashes/TABs in names/notes instead of escaping: t07 and smoke fail (part of control (e)).
8. M3 fix that escapes only quotes: e07 has backslash and TAB.
9. M6 fix that only applies direct parents' denies: e15 (deny two levels up).
10. M7 fix that only clears direct children: e16 (grandchild).
11. Putting the appt.cancel check before argument validation changes `appt-status A9 cancelled` from `unknown-appointment` to `denied` (t12; the README states the order).
12. Wrapping the import refusal as `import: line N: denied: ...` (per-row check that does not re-raise): README says a refusal is always exactly `ERROR denied: PERM`.

Behaviour that is easy to break while fixing, covered by ref_tests: t09 (3,000-row
import plus 700 commands, ~2 s on gold, must stay under 10 s), t10 (TAB
separators, trailing blanks, CRLF, blank lines inside a block, `.end` with
blanks), t11 (documented error texts), t04 (audit order of archive: appt.status
rows then customer.archive), t06/t13 (ordering of reports and exports).

## Notes

* Original passes every smoke and ref_tests case and fails all 20 ref_edge
  cases; each mutant fails only its own ref_edge cases (check_variants.py).
* Inputs are generated by make_inputs.py; outputs by build_private.sh from gold;
  public/src, mutants and control patch trees by make_variants.py (exact-text edits).
* The consistency check's "changed" test uses per-table write counters kept by
  TEMP triggers (not part of sqlite_master, rolled back with the savepoint).
* Precedence tests avoid ambiguous combinations: state checks (bad-transition,
  archived) vs conditional permissions are never tested together; import
  permission tests always use valid blocks with at least one row.
* Possible solver confusion: `import` with bad arguments still consumes its block
  (documented); t11 relies on it.
