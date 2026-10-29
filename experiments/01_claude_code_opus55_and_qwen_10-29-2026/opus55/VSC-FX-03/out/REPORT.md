# VSC-FX-03 root cause: docvault containment check

## Root causes
1. **READ / RUN (`Session._locate_file`)** checked containment with
   `vpaths.within_text`, a string-prefix test on the *unresolved* joined path.
   `..` parts (`../bob/x`), links pointing outside, and sibling folders that
   share a prefix (`alice` and `alice2`) all got past it. The resolved path
   was then handed to `guard`, which fired the invariant (exit 86). Because the
   check ran on text only, a missing target outside the root also gave
   `ERROR: not found` where it should give DENIED. This one helper is used for
   READ, for the RUN file itself, and for every READ/RUN inside a RUN file.
2. **LIST** ran `resolve_real` on the argument *before* alias expansion, so it
   only checked the literal `@name` text. The expanded path was resolved but
   never checked (`ALIAS b ../bob` + `LIST @b` listed someone else's folder,
   which hit the invariant). A missing outside target gave `not found`.
3. **EXPORT folder expansion (`archive.collect`)** followed links found while
   expanding folders without checking containment, so a link to an outside
   folder or file reached `guard.list_dir` / `guard.read_bytes` (invariant)
   instead of denying the whole line.
4. **EXPORT output file**: only `exports/` was resolved and checked. The
   archive path `exports/NAME.tar` was written without being re-checked after
   resolution, so a link at that location pointing outside the root hit the
   invariant on write.

## Fix (out/patch/)
* `commands.py::_locate_file`: alias-expand, then `vpaths.resolve_real`
  (realpath, then a separator-aware `within_real` check) before any existence check.
* `commands.py::cmd_list`: alias-expand first, then `resolve_real` on the
  expanded path; existence/folder checks come after.
* `archive.py::collect`: every location reached (start paths and anything
  reached while expanding, including dangling links, checked before existence)
  must pass `vpaths.within_real`, otherwise it raises `Denied`. Nothing has
  been written yet at that point, so the line stays all or nothing.
* `commands.py::cmd_export`: resolve and check `exports/NAME.tar` with
  `resolve_real` before creating the folder or writing.
Valid behaviour is unchanged: `..`, leading `/`, aliases and links that stay
inside the user root still work, and so do the exports skip, dedup by real
location and nested RUN semantics.

## Tests (out/tests/)
t01-t07 READ/LIST via `..`, links, aliases, missing outside targets, and the prefix
sibling; t08-t10 RUN file and commands inside RUN (own and inherited aliases);
t11-t14, t18 EXPORT via outside links (folder/file), all or nothing (old archive kept),
archive-file link, and prefix sibling; t15-t17 valid use that must keep working.
