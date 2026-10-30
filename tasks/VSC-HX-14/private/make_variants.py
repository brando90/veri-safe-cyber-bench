#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Derive public/src (the original program with all K=10 defects), the
mutants (gold plus exactly one defect each) and the patch trees of the
scorer controls from private/gold.  Deterministic, stdlib only.  Every edit
is an exact, unique text replacement, so a drift in gold fails loudly."""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
GOLD = os.path.join(HERE, "gold")

# ---------------------------------------------------------------- defects
# Each defect: list of (file, gold text, defective text).

D01_CIVIL = [("civil.py", '''    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
''', '''    yoe = (doe - doe // 1460 + doe // 36524) // 365
''')]

D02_CATS = [("fields.py", '''    return item.replace("\\\\", "\\\\\\\\").replace(",", "\\\\,")
''', '''    return item.replace(",", "\\\\,")
''')]

D03_VARINT = [("varint.py", '''    while n >= 0x80:
''', '''    while n > 0x80:
''')]

D04_OFFSET = [("offsets.py", '''    sign = "-" if minutes < 0 else "+"
''', '''    sign = "-" if hours < 0 else "+"
''')]

D05_WEEKLY = [("expand.py", '''    ws = civil.week_start(start)
''', '''    ws = start
''')]

D06_SNAP = [("timeparse.py", '''    if h == 24:
        h = 0
        y, mo, d = civil.civil_from_days(civil.days_from_civil(y, mo, d) + 1)
''', '''    if h == 24:
        h = 0
''')]

D07_NATURAL = [("names.py", '''def natural_key(text):
    key = []
    for chunk in CHUNK_RE.findall(text):
        if chunk[0] in "0123456789":
            key.append((1, int(chunk), len(chunk)))
        else:
            key.append((0, 0, chunk))
    return key
''', '''def natural_key(text):
    key = []
    for chunk in CHUNK_RE.findall(text)[:2]:
        if chunk[0] in "0123456789":
            key.append((1, int(chunk), len(chunk)))
        else:
            key.append((0, 0, chunk))
    return key
''')]

D08_REF = [("ids.py", '''    digits = []
    while True:
        n, r = divmod(n, 32)
        digits.append(ALPHABET[r])
        if n == 0:
            break
    return "".join(reversed(digits))
''', '''    width = 1 if n < 32 else int(math.log(n, 32)) + 1
    return "".join(ALPHABET[(n >> (5 * i)) & 31] for i in range(width - 1, -1, -1))
''')]

D09_RESCHEDULE = [("events.py", '''    ev.start, ev.raw, ev.rule = start, raw, rule
    drop_stale_skips(ev)
''', '''    ev.rule = rule
    drop_stale_skips(ev)
    ev.start, ev.raw = start, raw
''')]

D10_TITLE = [("fields.py", '''    return re.sub(r"[ \\t]+", " ", text.strip(" \\t"))
''', '''    text = re.sub(r"\\t", " ", text.strip(" \\t"))
    return text.replace("  ", " ")
''')]

DEFECTS = {
    "M01_civil_cycle_end": D01_CIVIL,
    "M02_category_backslash": D02_CATS,
    "M03_varint_boundary": D03_VARINT,
    "M04_offset_sign": D04_OFFSET,
    "M05_weekly_anchor": D05_WEEKLY,
    "M06_snap_carry": D06_SNAP,
    "M07_natural_ids": D07_NATURAL,
    "M08_ref_width": D08_REF,
    "M09_move_skips": D09_RESCHEDULE,
    "M10_title_blanks": D10_TITLE,
}

# ---------------------------------------------------------------- control-only edits
# Over-aggressive "fixes" that change documented behaviour:
OA_TITLE_SPLIT = [("fields.py", '''    return re.sub(r"[ \\t]+", " ", text.strip(" \\t"))
''', '''    return " ".join(text.split())
''')]
OA_OFFSET_Z = [("offsets.py", '''    hours = int(minutes / 60)
''', '''    if minutes == 0:
        return "Z"
    hours = int(minutes / 60)
''')]
OA_YEARLY_MARCH = [("expand.py", '''        yield civil.days_from_civil(y, sm, min(sd, civil.days_in_month(y, sm)))
''', '''        if sd > civil.days_in_month(y, sm):
            yield civil.days_from_civil(y, sm + 1, 1)
        else:
            yield civil.days_from_civil(y, sm, sd)
''')]
OA_BUSY_STRICT = [("busy.py", '''        if out and start <= out[-1][1]:''', '''        if out and start < out[-1][1]:''')]
OA_SKIP_KEEP = [("events.py", '''    ev.skips = [d for d in ev.skips if d in live]
''', '''    ev.skips = [d for d in ev.skips if d in live or d == ev.skips[-1]]
''')]
# Weakened self-check: the consistency check is turned off.
OA_NO_CHECK = [("invariant.py", '''def full_check(w, everything=False):
    store = w.store
''', '''def full_check(w, everything=False):
    return
    store = w.store
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
        assert text.count(old) == 1, (dest, fname, old[:70])
        with open(p, "w") as fh:
            fh.write(text.replace(old, new))
    # D08 needs the math import in ids.py
    ids_p = os.path.join(dest, "ids.py")
    with open(ids_p) as fh:
        text = fh.read()
    if "math.log" in text and "import math" not in text:
        text = text.replace('"""\nALPHABET', '"""\nimport math\n\nALPHABET', 1)
        assert "import math" in text
        with open(ids_p, "w") as fh:
            fh.write(text)


def flat(*groups):
    out = []
    for g in groups:
        out.extend(g)
    return out


def with_defects(*names):
    """The edits of the named defects only (a tree where every other one is fixed)."""
    return flat(*(edits for name, edits in DEFECTS.items() if name in names))


def main():
    make_tree(os.path.join(TASK, "public", "src"), flat(*DEFECTS.values()))
    mroot = os.path.join(HERE, "mutants")
    if os.path.exists(mroot):
        shutil.rmtree(mroot)
    for name, edits in DEFECTS.items():
        make_tree(os.path.join(mroot, name), edits)
    ct = os.path.join(HERE, "controls")
    trees = {
        # (d) everything fixed except the two hardest variants
        "d_partial": with_defects("M08_ref_width", "M09_move_skips"),
        # (e) every fix applied, plus changes of documented behaviour
        "e_overaggressive": flat(OA_TITLE_SPLIT, OA_OFFSET_Z, OA_YEARLY_MARCH),
        "e2_overaggressive_listings": flat(OA_BUSY_STRICT, OA_SKIP_KEEP),
        # (g) the self-check silenced, defects left in
        "g_check_disabled": flat(*DEFECTS.values(), OA_NO_CHECK),
    }
    for name, edits in trees.items():
        make_tree(os.path.join(ct, name, "patch"), edits)
    print("public/src, %d mutants and %d control trees written" % (len(DEFECTS), len(trees)))


if __name__ == "__main__":
    main()
