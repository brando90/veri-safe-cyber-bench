# VSC-HX-12 author notes (private)

crateyard: toy package-registry simulator. 31 Python modules (about 1,900
lines) plus a 140-line README. Lever (hard tier v4, "defects with no README
rule"): README.md and INSTRUCTION.md describe the commands and the I/O format
only in general terms and state none of the rules the defects break. Every
intended behaviour follows from the program's own dominant convention: the
same check or helper used at the other sites, the consistency check
(invariant.py, run after every command, exit 86), the error table
(errors.MESSAGES) and the policy tables.

Wiring: `World` holds clock, users, registry, quota, audit, locks; the
dispatcher (world.COMMANDS) names each positional argument ACTOR (the user
making a change), VIEWER (a reader, `-` = anonymous) or USER/NAME (a user
being looked at). Roles and what they may do are in perms.ACTION_ROLE with two
exception tables; registry-wide exceptions are in policy.py.

## The defects (K = 9, one mutant each in private/mutants)

| Mutant | Where | Defect | Convention the correct behaviour follows (derivation) |
|---|---|---|---|
| M01_tag_actor | tags._change (tag add / tag rm) | ACTOR resolved with `users.get` (no disabled check); a disabled user can still move or delete tags | All 16 other state-changing handlers resolve their ACTOR with `users.actor()` (= `get` + `disabled` error); `get` is used only for USER/NAME arguments (targets). The usage strings of `tag add`/`tag rm` call the argument ACTOR. Expected: `error: user NAME is disabled`, nothing changes. |
| M02_prune_refund | lifecycle.cmd_prune | refund `size // 1024` (floor) | publish charges `units.kib_ceil(size)`; unpublish and package delete refund `kib_ceil`; `Release.kib` is `kib_ceil`; invariant.full_check compares each publisher's usage with the sum of `kib_ceil(size)` over live releases, so the original exits 86 after pruning a release whose size is not a KiB multiple. Expected: refund `kib_ceil`. |
| M03_latest_prerelease | publish.cmd_publish | the managed `latest` tag moves to a new release if it is higher, pre-releases included | `Package.recompute_latest` (used by yank, unyank, unpublish, prune) picks the highest non-yanked release without a pre-release part; `tags.MANAGED` makes `latest` registry-owned; requirements skip pre-releases unless asked. In the original a pre-release publish moves `latest` and the next yank/unyank of any release moves it back, so the publish path disagrees with every recompute. Expected: a pre-release never becomes `latest` (same as calling `recompute_latest`). |
| M04_fetch_req_guard | fetch.pick | result of `reqs.parse` used without the None check; a malformed requirement ends in a traceback | reqs.parse is documented to return None for text it cannot read; the three other callers (publish.parse_deps, resolver.cmd_resolve, lockfile.parse_roots) all raise `CommandError("bad_req", spec)`. Expected: `error: bad requirement 'SPEC'`. |
| M05_remove_last_owner | accounts.cmd_remove | removing a user strips their roles even when they are the only owner of a package (invariant fires) | invariant: every package has at least one owner; owners.cmd_remove and owners.cmd_accept (downgrade) refuse with `last_owner` via `perms.owner_count`. Expected: `error: cannot remove the last owner of PKG` (first such package in name order), nothing changes. |
| M06_invite_deadline | owners.cmd_accept | `now > expires_at` inline | `timeutil.expired` (`now >= deadline`) is used for the unpublish grace window, the embargo, and the pending-invite listing of the very same invites (`invites` shows none at the deadline instant while `owner accept` still works). Expected: invite expired at its deadline. |
| M07_top_size_order | stats.cmd_top, `size` | sorted on `(value, name)` with `reverse=True`: ties come out in descending name order | `stats.rank` (`(-value, name)`, ties ascending) is used by the other three rankings; smoke s4 shows a tie (`cli` before `http`). Expected: `rank(...)`. |
| M08_unpublish_tags | lifecycle.cmd_unpublish | release deleted inline (`del` + `recompute_latest`), tags pointing at it are left behind (invariant fires) | `Package.drop_release` (used by prune) deletes the release, drops every tag pointing at it and recomputes `latest`; invariant: every tag points to an existing release. Expected: such tags silently disappear. |
| M09_dependents_visibility | info.cmd_dependents | lists every package that depends on PKG, including private ones the viewer cannot read | every other listing filters with `perms.can(viewer, p, "read")`: `search`, `top` (stats.visible), `top dependents` counts (stats.dependents_of), and single-package reads refuse unreadable private packages as `unknown package`. Expected: unreadable dependents omitted. |

Mix: findable inside one function once the convention is known: M04, M06,
M07. Need following a convention across 3+ modules: M01 (world usage strings,
users, 16 handlers), M02 (units, publish, lifecycle, registry, invariant), M03
(registry, publish, tags, reqs), M05 (accounts, owners, perms, invariant),
M08 (registry, lifecycle, invariant), M09 (info, stats, perms). Number/time
conventions: M02 (rounding), M06 (deadline boundary), M07 (ordering). Three
fire the consistency check (M02, M05, M08), one ends in a traceback (M04), five
only print the wrong thing (M01, M03, M06, M07, M09).

## Intended fix (= private/gold)

* tags._change: `actor = w.users.actor(cmd.arg(0))`.
* lifecycle.cmd_prune: `w.quota.adjust(rel.publisher, -units.kib_ceil(rel.size))`.
* publish.cmd_publish: `if not ver.pre and (cur is None or ...)` (calling `pkg.recompute_latest()` is equivalent).
* fetch.pick: `if req is None: raise CommandError("bad_req", spec)`.
* accounts.cmd_remove: refuse with `last_owner` before changing anything.
* owners.cmd_accept: `if timeutil.expired(w.now, inv.expires_at)`.
* stats.cmd_top size: `rank([...], n)`.
* lifecycle.cmd_unpublish: `pkg.drop_release(rel.text)`.
* info.cmd_dependents: skip packages with `not perms.can(w, viewer, other, "read")` (or use `stats.dependents_of`).

## Decoys (apparent deviations that are deliberate exceptions in a data table)

1. perms.PUBLIC_ACTIONS: `fetch`/`read` of a public package needs no role, even anonymous (t03, smoke s1). Control e.
2. perms.ADMIN_ACTIONS: an admin may yank, unyank, unpublish, manage roles and visibility without a role, but not publish or tag (t05). Control e2.
3. policy.UNPUBLISH_GRACE: pre-releases have no grace limit, stable releases 72 h (t06, e16, smoke s3). Control e.
4. policy.YANKED_SELECTABLE: an exact `=V` requirement still selects a yanked release (t07). Control e.
5. policy.EMBARGO_BYPASS_ROLES: owners and maintainers see embargoed releases, readers and others do not (t08). Control e2.
6. perms.ACTION_ROLE: `yank` needs maintainer but `unyank`/`unpublish` need owner (t10). Control e2.
7. policy.INVITE_TTL_MAX: a different lifetime cap per offered role (t09).
8. tags.MANAGED: `latest` cannot be set or removed by hand (t11).

Other code that looks odd but is right: `users.get` for USER/NAME arguments (a
disabled user can be invited, shown, given a quota); `owner accept` has no
role check (the invite is the permission); `quota.check` allows reaching the
limit exactly (t12); `info` shows embargoed releases with `embargo=T` (only
resolution is held back); legacy.py is dead v1 code.

## Traps (each caught by a hidden case; see private/CONTROLS.md)

1. "Hardening" any table exception above: t03, t05, t06, t07, t08, t10 (controls e, e2).
2. Harmonising the invite deadline the wrong way (listing changed to `>`): e11, e12 (control g).
3. Harmonising the ranking the wrong way (shared `rank` changed to the reverse sort): smoke s4, t04, t20, e13, e14 (control h).
4. Fixing M02 by flooring everywhere / changing the invariant: smoke s1/s3 quota lines, t12.
5. Fixing M05 by transferring ownership or deleting packages instead of refusing: e09, e10.
6. Fixing M08 by re-pointing tags instead of dropping them: e15, e16.
7. Fixing M04 with a different message or by treating bad text as `*`: e07, e08.

## Notes

* README and INSTRUCTION.md name no rule a defect breaks; NOTES above give
  the derivation from code for each one. No comment or docstring in
  public/src marks a defect site.
* Original passes every smoke case and fails all 18 ref_edge cases plus one
  ref_tests case (t06, which touches M03). Each mutant fails only its own two
  ref_edge cases (M03 also t06) and no smoke case (check_variants.py).
* Inputs come from private/make_inputs.py; outputs from private/build_private.sh
  (gold run in a fresh dir); public/src, mutants and control patch trees from
  private/make_variants.py (exact-text edits of gold). t15 is a 1,600-command
  generated session (fixed seed), about 1 s on gold.
