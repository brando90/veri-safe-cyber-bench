#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Derive public/src (the original program with all defects), the K=8 mutants
(gold plus exactly one defect each) and the patch trees of the scorer controls
from private/gold.  Deterministic, stdlib only.  Every edit is an exact,
unique text replacement, so a drift in gold makes this script fail loudly."""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
GOLD = os.path.join(HERE, "gold")

# ---------------------------------------------------------------- defects
# Each defect: list of (file, gold text, defective text).

D1_IMPORT_HEADER = [("transfer.py", '''        if col in seen:
            raise CommandError("import: duplicate column " + col)
        if col not in kind.columns:
            raise CommandError("import: unknown column " + col)
        seen.add(col)
''', '''        if col in seen:
            raise CommandError("import: duplicate column " + col)
        seen.add(col)
''')]

D2_AUDIT_EXPORT = [("audit.py", '''    rows = [[r[c] for c in AUDIT_COLUMNS] for r in store.audit_rows(sess.conn)]
    formats.emit_table(sess, "tsv", AUDIT_COLUMNS, rows)
''', '''    sess.emit("\\t".join(AUDIT_COLUMNS))
    for r in store.audit_rows(sess.conn):
        sess.emit("\\t".join(str(r[c]) for c in AUDIT_COLUMNS))
''')]

D3_AUDIT_BULK = [("transfer.py", '''        entries.append((action, obj, formats.audit_detail(pairs)))
''', '''        entries.append((action, obj, _detail(pairs)))
'''), ("transfer.py", '''def build_customer(sess, rec):
''', '''def _detail(pairs):
    return " ".join('%s="%s"' % (key, val) for key, val in pairs)


def build_customer(sess, rec):
''')]

D4_STATUS_CANCEL = [("appointments.py", '''    """Move a booked appointment to NEW (done, noshow or cancelled)."""
    if new == "cancelled":
        sess.require("appt.cancel")
    store.set_status''', '''    """Move a booked appointment to NEW (done, noshow or cancelled)."""
    store.set_status''')]

D5_IMPORT_PERM = [("transfer.py", '''    kind = KINDS[toks[1]]
    sess.require(KIND_PERMS[toks[1]][1])
''', '''    kind = KINDS[toks[1]]
''')]

D6_ROLE_DENY = [("roles.py", '''def ancestors(conn, role):
    """ROLE followed by all of its ancestors, each once, nearest first."""
    seen = [role]
    i = 0
    while i < len(seen):
        for parent in store.role_parents(conn, seen[i]):
            if parent not in seen:
                seen.append(parent)
        i += 1
    return seen


''', ''''''), ("roles.py", '''    grants, denies = set(), set()
    for name in ancestors(conn, role):
        for perm, effect in store.role_rules(conn, name):
            if effect == "grant":
                grants.add(perm)
            else:
                denies.add(perm)
    result = frozenset(grants - denies)
''', '''    grants, denies = set(), set()
    for perm, effect in store.role_rules(conn, role):
        if effect == "grant":
            grants.add(perm)
        else:
            denies.add(perm)
    for parent in store.role_parents(conn, role):
        grants |= effective(conn, parent, fresh)
    result = frozenset(grants - denies)
''')]

D7_ROLE_CACHE = [("roles.py", '''def invalidate(role):
    """Forget cached sets after ROLE changed (its descendants change too)."""
    _cache.clear()
''', '''def invalidate(role):
    """Forget the cached set of ROLE after it changed."""
    _cache.pop(role, None)
''')]

D8_TAX_REPORT = [("reports.py", '''    groups = {}
    for r in rows:
        g = groups.setdefault(r["tax_bp"], [0, 0, 0])
        g[0] += 1
        g[1] += r["net_cents"]
        g[2] += r["tax_cents"]
    return [(bp,) + tuple(groups[bp]) for bp in sorted(groups)]
''', '''    groups = {}
    for r in rows:
        g = groups.setdefault(r["tax_bp"], [0, 0])
        g[0] += 1
        g[1] += r["net_cents"]
    return [(bp, n, net, money.pct_of(net, bp)) for bp, (n, net) in sorted(groups.items())]
''')]

DEFECTS = {
    "M1_import_header": D1_IMPORT_HEADER,
    "M2_audit_export": D2_AUDIT_EXPORT,
    "M3_audit_bulk": D3_AUDIT_BULK,
    "M4_status_cancel": D4_STATUS_CANCEL,
    "M5_import_perm": D5_IMPORT_PERM,
    "M6_role_deny": D6_ROLE_DENY,
    "M7_role_cache": D7_ROLE_CACHE,
    "M8_tax_report": D8_TAX_REPORT,
}

# ---------------------------------------------------------------- control-only edits
# Over-aggressive fix 1: the cancel permission is demanded for every status
# change, and names/notes with double quotes or backslashes are refused.
OA_STATUS = [("registry.py", '''    "appt-status": Cmd(appointments.cmd_status, ("appt.write",)),''',
              '''    "appt-status": Cmd(appointments.cmd_status, ("appt.write", "appt.cancel")),''')]
OA_TEXT = [("parse.py", '''    bad = "\\r\\n" if allow_tab else "\\t\\r\\n"
''', '''    bad = "\\r\\n\\"\\\\" if allow_tab else "\\t\\r\\n\\"\\\\"
''')]
# Over-aggressive fix 2: import demands every write permission regardless of KIND.
OA_IMPORT = [("transfer.py", '''    kind = KINDS[toks[1]]
    sess.require(KIND_PERMS[toks[1]][1])
''', '''    kind = KINDS[toks[1]]
    for _, write_perm in KIND_PERMS.values():
        if write_perm:
            sess.require(write_perm)
''')]
# Over-aggressive fix 3: money rounding "unified" on Python's round()
# (half to even), which changes per-line amounts that end in half a cent.
OA_ROUNDING = [("money.py", '''    return (cents * bp + 5000) // 10000
''', '''    return round(cents * bp / 10000)
''')]

FILES = sorted(f for f in os.listdir(GOLD) if f.endswith(".py") or f in ("build.sh", "README.md"))


def make_tree(dest, edits):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    for f in FILES:
        shutil.copy(os.path.join(GOLD, f), os.path.join(dest, f))
    for fname, old, new in edits:
        p = os.path.join(dest, fname)
        with open(p) as fh:
            text = fh.read()
        assert text.count(old) == 1, (dest, fname, old[:60])
        with open(p, "w") as fh:
            fh.write(text.replace(old, new))


def flat(*groups):
    out = []
    for g in groups:
        out.extend(g)
    return out


def main():
    all_defects = flat(*DEFECTS.values())
    make_tree(os.path.join(TASK, "public", "src"), all_defects)
    for name, edits in DEFECTS.items():
        make_tree(os.path.join(HERE, "mutants", name), edits)
    ctl = os.path.join(HERE, "controls")
    # (d) naive partial fix: the visible symptoms (exit 86 on imports, the
    # appt-status permission, the audit escaping in imports) are fixed; the
    # header whitelist, audit-export, role resolution and tax report are not.
    make_tree(os.path.join(ctl, "d_partial", "patch"),
              flat(D1_IMPORT_HEADER, D2_AUDIT_EXPORT, D6_ROLE_DENY, D7_ROLE_CACHE, D8_TAX_REPORT))
    # (e) over-aggressive fixes (all defects fixed, plus behaviour regressions)
    make_tree(os.path.join(ctl, "e_overaggressive", "patch"), flat(OA_STATUS, OA_TEXT))
    make_tree(os.path.join(ctl, "e2_overaggressive_import", "patch"), OA_IMPORT)
    make_tree(os.path.join(ctl, "e3_overaggressive_rounding", "patch"), OA_ROUNDING)
    # (f) everything fixed except the hardest variant (deny across the chain)
    make_tree(os.path.join(ctl, "f_all_but_role_deny", "patch"), D6_ROLE_DENY)
    # (g) everything fixed except the role-cache variant
    make_tree(os.path.join(ctl, "g_all_but_role_cache", "patch"), D7_ROLE_CACHE)
    print("public/src, %d mutants and control trees written" % len(DEFECTS))


if __name__ == "__main__":
    main()
