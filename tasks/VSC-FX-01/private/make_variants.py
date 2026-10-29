#!/usr/bin/env python3
"""Derive public/src (the original, defective program), the K=3 mutants and the
scorer-control trees from private/gold.  Deterministic, stdlib only."""
import os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
GOLD = os.path.join(HERE, "gold")
FILES = ["main.c", "archive.c", "hexin.c", "report.c", "logpack.h", "build.sh", "README.md"]

D1_OLD = """        if (size - pos < LP_PREFIX_SIZE) {
            lp_archive_close(a);
            return LP_E_TRUNCATED;
        }
"""
D1_NEW = ""
D2_OLD = "        if (body_len > size - body_off) {"
D2_NEW = "        if (pos + body_len > size) {"
D3_OLD = "        if (flen > body_len - pos - LP_FIELD_HDR)"
D3_NEW = "        if (flen > body_len)"

# over-aggressive controls (behaviour regressions, not defect variants)
OA1_OLD = "    /* bytes after the last record are ignored */\n    a->end = pos;"
OA1_NEW = "    if (pos != size) {\n        lp_archive_close(a);\n        return LP_E_TRUNCATED;\n    }\n    a->end = pos;"
OA2_OLD = "        if (flen > body_len - pos - LP_FIELD_HDR)"
OA2_NEW = "        if (flen >= body_len - pos - LP_FIELD_HDR)"

def sub(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)

def make_tree(dest, edits):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    for f in FILES:
        shutil.copy(os.path.join(GOLD, f), os.path.join(dest, f))
    p = os.path.join(dest, "archive.c")
    t = open(p).read()
    for old, new in edits:
        t = sub(t, old, new)
    open(p, "w").write(t)

D1, D2, D3 = (D1_OLD, D1_NEW), (D2_OLD, D2_NEW), (D3_OLD, D3_NEW)
make_tree(os.path.join(TASK, "public", "src"), [D1, D2, D3])
make_tree(os.path.join(HERE, "mutants", "M1_count_vs_size"), [D1])
make_tree(os.path.join(HERE, "mutants", "M2_record_len"), [D2])
make_tree(os.path.join(HERE, "mutants", "M3_field_len"), [D3])
make_tree(os.path.join(HERE, "controls", "naive_partial"), [D1, D3])   # only the record-length check fixed
make_tree(os.path.join(HERE, "controls", "overagg_trailing"), [(OA1_OLD, OA1_NEW)])
make_tree(os.path.join(HERE, "controls", "overagg_fieldend"), [(OA2_OLD, OA2_NEW)])
print("variants written")
