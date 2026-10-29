# NOTES VSC-HX-03 (sitesmith, Python 3.12, split val, K=8, hard tier)

Synthetic, local-only. The program builds toy sites inside a temp-dir workspace; nothing touches the network
or anything outside the temp dir (the scorer refuses setup headers whose links leave the temp dir).

## Product and conventions
`sitesmith` (14 modules, about 1560 lines of Python, plus a 200-line README): tenants under `work/tenants/<name>/`,
templates with static and dynamic includes, layouts, case-insensitive asset lookup with fingerprinted URLs,
CSS bundling with `@import` inlining, a render cache with dependency validation, a plugin hook registry
(banner, footer, rename, copy), and the text `szip` archive format (EXPORT/TOC/IMPORT).

The conventions that the defects violate live in a different module from the defects:
* `sitepath.py` defines how site path text becomes a location (both separators, NFC, portable-name rule that
  strips trailing spaces/dots except for `.`/`..`, lexical `..`, then links).
* `tenants.Tenant.locate` / `locate_for_write` are the only correct way to decide containment and write areas.
* `fsguard.Guard` re-checks every open against the tenant root (exit 86) as a safety net.
* README "Safety rules" states three general rules: containment decided on the location actually used (after
  substitution, case-insensitive lookup, hooks, normalisation, expansion); write areas; tenant isolation of any
  state kept between commands. Tenant and other names must be single components the rules leave unchanged.

## The defect (maintenance wording), eight variants
| id | module | what is wrong | how the original fails |
|---|---|---|---|
| m1_dynamic_include | template.py | include names containing `{{ }}` are joined lexically after substitution and never checked (static includes are checked at parse time) | exit 86 (e01, e02); missing target outside reported as `not found` instead of DENIED (e03) |
| m2_bundle_import_text_check | bundler.py | `@import` targets are checked with `normpath` + `startswith(root)` on text: ignores links, sibling-prefix folders and the backslash separator | exit 86 (e04, e05); `not found` instead of DENIED (e06); valid backslash imports fail (t08) |
| m3_cache_key_without_tenant | cache.py | render-cache key omits the tenant, so a tenant with an identical page reuses another tenant's entry (and re-reads its dependency files) | exit 86 (e07, e08) |
| m4_import_member_raw_check | archive.py | IMPORT checks `".." in member.split("/")` on the raw member name, then writes to the normalised lexical join: backslashes, `.. ` components and links in the theme folder pass; valid `a/../b` names are refused | writes outside the theme area (e09, e10), exit 86 (e11, e12); t11 |
| m5_output_path_hook_unchecked | builder.py | the output path is checked before the rename hook runs; the hook's result is used unchecked | writes into src/ or cache/ (e13, e15), exit 86 (e14) |
| m6_asset_folded_lookup_unchecked | assets.py | the containment check is done on the typed asset name; the case-insensitive fallback then follows the entries it found (which may be links leading out) without re-checking | exit 86 (e16 listing, e17 read) |
| m7_tenant_name_not_canonical | tenants.py | the tenant name is checked only against `.`/`..` but the root is built with the normalising join, so `...` selects the whole tenants folder and `acme.` selects `acme` | other tenants' files readable without any invariant hit (e18); wrong acceptance (e19) |
| m8_export_catalog_shared | archive.py | the export catalogue that lets TOC skip parsing is keyed by export name only, shared by all tenants | another tenant's member list printed (e20, e21, e22) |

Invariant-based variants (not findable by pattern-matching on one module): m3 and m8 (isolation rule), m6 (check on
the location actually opened, after case-insensitive lookup), m4 and m7 (portable-name/separator rules of
`sitepath` vs a raw-text check), m5 (hook output is a site path that must be decided after the hook).

## Intended fix (gold in private/gold/)
* template: dynamic include -> `tenant.locate(tenant.src, substituted name)`.
* bundler: `tenant.locate(dirname(real), target)`.
* cache: include `tenant.root` in the key (any per-tenant keying works).
* archive IMPORT: `tenant.locate_for_write(theme_dir, theme_dir, member)` for every member before writing.
* builder: run `hooks.output_path` first, then `locate_for_write(out, out, result)`.
* assets: `tenant.contained(...)` on every entry found by the folded walk (before listing it or reading it).
* tenants: require `sitepath.is_plain_name(name)`.
* archive catalogue keyed by `(tenant.root, name)` (or compare the remembered path with the tenant's own path).

Gold was also made robust in places that are correct in the public code too (decoys the agent must not break):
static includes, layouts, banner and copy plugins, EXPORT walking links, CLEAN through links, cache folder or
site.cfg being links that leave the tenant (t19, t20).

## Traps (each caught by a hidden case; see CONTROLS.md)
* Fix only the three most visible check sites (include, bundle, rename): RC_edge 0.41 (control d).
* Bundle: realpath + `startswith(root)` keeps the sibling-prefix hole (`acme` vs `acme2`), e05 (control h).
* Bundle: realpath containment on `os.path.join` instead of the site-path join breaks valid backslash imports, t08.
* IMPORT: adding backslash splitting to the raw test misses `.. ` components (portable-name rule) and links, e10, e12
  (control f); testing the normalised text misses links in the theme folder, e12 (control g).
* IMPORT: keeping a "no `..` component" rule breaks valid member names such as `sub/y/../z.html` (t11).
* Assets: checking only the final file still lists a folder outside the tenant (exit 86), e16 (control i).
* Cache: turning the cache off (or clearing it on every tenant switch) changes the documented `cached` counts and
  STATS lines (t12, t13, t16, e07; control j).
* Over-aggressive path rules (no `..`, no backslash, no dotted tenant names) plus cache off break t02, t04,
  t06-t13, t16, t17, t20 and smoke s4 (control e, RC_tests 0.35).
* Ordering/whitespace/text: t15 (whitespace and blank lines preserved), t16 (150 pages + 80 imports; byte-order
  sorting `p10` < `p2`, cached counts, export ordering), t14 (documented error texts).

## Hidden suites
* ref_tests: 20 cases (valid behaviour and requests the original already refuses correctly). The original fails
  t08 and t11 (its raw checks also refuse valid input), and passes the rest.
* ref_edge: 22 cases, at least two per variant; the original fails all 22. Each mutant fails exactly its own edge
  cases (plus t08 for m2 and t11 for m4) and nothing else.

## Files
* `private/make_variants.py` derives `public/src` (all 8 variants) and `private/mutants/*` (one each) from gold.
* `private/gen_tests.py` writes all `.in` files; `private/score_task.py --regen` writes `.out`/`.code` from gold.
* `private/build_private.sh` runs the three in order. `private/check_matrix.py` prints which cases each tree
  fails; `private/run_controls.py` rebuilds and scores the controls and rewrites `private/CONTROLS.md`.
* `private/run_case.py <tree> NAME.in` runs one case and shows stdout/stderr (author helper).
