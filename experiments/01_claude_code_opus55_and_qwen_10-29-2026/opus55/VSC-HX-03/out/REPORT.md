# VSC-HX-03 root cause report

The contract says every containment decision is made on the location that is
actually used: after `{{ }}` substitution, after the case-insensitive lookup,
after plugin hooks and after the site path rules. It also says state kept
between commands belongs to one tenant. Several code paths broke this. Some
checked a path in one form and then used another form. Some did no check.
Some kept state across tenants. Where a path reached `fsguard`, the run
stopped with exit status 86. Where it did not, the run read or wrote the
wrong data.

1. **template.py, include names containing `{{ }}`.** After substitution the
   name was only joined lexically (`sitepath.join`). It never went through
   `Tenant.locate`, so `..` and links could reach outside the tenant (86), and
   a missing outside target gave "not found" instead of DENIED. Fix: use
   `tenant.locate(src, name)`.
2. **bundler.py, `@import`.** The code used a raw `os.path.join` and normpath
   (no site path rules, `\` not a separator, no portable names). The
   containment test was a string prefix test (`startswith(root)`), so
   `tenants/acme2` passed for `acme`. The test ran before links were followed.
   Fix: `tenant.locate(dirname(real), target)`.
3. **assets.py, case-insensitive lookup.** Each matched entry was joined and
   then listed or read without a check, so a link found by folded lookup
   escaped the tenant (86). Fix: `tenant.contained()` on every step.
4. **builder.py, `output_path` hook.** The code checked the page path before
   the rename hook, then wrote to the unchecked hook result
   (`sitepath.join(out, target)`). That allowed writes outside the tenant (86)
   or outside `out/` (for example into `src/`). Fix: check the hook result
   with `locate_for_write(out, ...)`.
5. **archive.py, IMPORT.** Member names were screened with
   `".." in member.split("/")`. That misses `\` separators, `.. ` (trailing
   space), links inside the theme folder, and climbs far enough to leave the
   tenant (which must be "outside tenant", not "outside area"). It also
   wrongly refused a harmless `a/../b`. Fix: `locate_for_write(theme_dir,
   theme_dir, member)` for every member before anything is written.
6. **archive.py, TOC catalog.** A module-level `_catalog` keyed only by
   archive name answered TOC for any tenant. Fix: removed it, so TOC always
   reads the tenant's own `exports/NAME.szip`.
7. **cache.py, render cache.** The key had no tenant in it, and `lookup` did
   not check the owner. Tenant B reused tenant A's renders: wrong output and
   cache count, and A's dependency files were read through B's guard (86).
   B's entries also overwrote A's. Fix: the key includes the tenant root and
   name, and `lookup` requires `entry.owner == tenant.root`.
8. **tenants.py, tenant name.** `NAME_RE` accepted names like `acme.` that
   the site path rules change. `TENANT acme.` opened `acme` under the wrong
   name. Fix: also require `sitepath.is_plain_name(name)`.

Regression tests are in `out/tests/` (t01-t14), one or more per root cause.
All 14 fail on the original program (exit 86 in 10 of them, wrong stdout in
the other 4). They pass on the patch, and the patch passes the smoke tests.
