#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Derive public/src (the original program with all K=10 slips), the mutants
(gold plus exactly one slip each) and the patch trees of the scorer controls
from private/gold.  Deterministic, stdlib only.  Every edit is an exact,
unique text replacement, so a drift in gold fails loudly."""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
GOLD = os.path.join(HERE, "gold")

# ---------------------------------------------------------------- slips
# Each slip: list of (file, gold text, defective text).

D01_FIELD_SPLIT = [("records.py", '''        name, sep, value = token.partition("=")
''', '''        name, sep, value = token.rpartition("=")
''')]

D02_PREFIX_STRIP = [("names.py", '''    return fold(name).removeprefix(PREFIX)
''', '''    return fold(name).lstrip(PREFIX)
''')]

D03_MASK_TAIL = [("maskers.py", '''    return MASK_CHAR * (len(value) - keep) + value[len(value) - keep:]
''', '''    return MASK_CHAR * (len(value) - keep) + value[-keep:]
''')]

D04_SCRUB_FLAGS = [("scanner.py", '''    text = re.sub(PAIR, _mask_pair, text, flags=re.IGNORECASE)
''', '''    text = re.sub(PAIR, _mask_pair, text, re.IGNORECASE)
''')]

D05_PREFIX_CLOSURE = [("policy.py", '''                checks.append((action, lambda base, p=prefix: base.startswith(p)))
''', '''                checks.append((action, lambda base: base.startswith(prefix)))
''')]

D06_LIMIT_ZERO = [("store.py", '''        return self.limits.get(source, self.default_limit)
''', '''        return self.limits.get(source) or self.default_limit
''')]

D07_PURGE_LOOP = [("store.py", '''        keep, removed = [], []
        for record in self.records:
            if stamp.older_than(now, record.when, days):
                removed.append(record.id)
            else:
                keep.append(record)
        self.records = keep
''', '''        removed = []
        for record in self.records:
            if stamp.older_than(now, record.when, days):
                removed.append(record.id)
                self.records.remove(record)
''')]

D08_TEMP_POLICY = [("policy.py", '''        temp = copy.deepcopy(self)
''', '''        temp = copy.copy(self)
''')]

D09_SHARE_FORMAT = [("reports.py", '''    tenths = (part * 2000 + whole) // (2 * whole)
    return "%d.%d" % divmod(tenths, 10)
''', '''    return "%.1f" % (100.0 * part / whole)
''')]

D10_RANK_ORDER = [("reports.py", '''    return sorted(counts.items(), key=lambda row: (-row[1], row[0]))
''', '''    rows = sorted(((count, name) for name, count in counts.items()), reverse=True)
    return [(name, count) for count, name in rows]
''')]

DEFECTS = {
    "M01_field_split": D01_FIELD_SPLIT,
    "M02_prefix_strip": D02_PREFIX_STRIP,
    "M03_mask_tail": D03_MASK_TAIL,
    "M04_scrub_flags": D04_SCRUB_FLAGS,
    "M05_prefix_closure": D05_PREFIX_CLOSURE,
    "M06_limit_zero": D06_LIMIT_ZERO,
    "M07_purge_loop": D07_PURGE_LOOP,
    "M08_temp_policy": D08_TEMP_POLICY,
    "M09_share_format": D09_SHARE_FORMAT,
    "M10_rank_order": D10_RANK_ORDER,
}

# ---------------------------------------------------------------- control-only edits
# Over-aggressive "fixes" that change documented behaviour (decoys "hardened"):
OA_AGE_EXACT = [("stamp.py", '''    return now - when > timedelta(days=days)
''', '''    return now - when >= timedelta(days=days)
''')]
OA_WINDOW_INCLUSIVE = [("windows.py", '''        while t - times[lo] >= window:
''', '''        while t - times[lo] > window:
''')]
OA_AVERAGE_HALF_UP = [("reports.py", '''len(per_source), round(total / len(per_source))))''',
                       '''len(per_source), (2 * total + len(per_source)) // (2 * len(per_source))))''')]
OA_CLEAN_ID = [("names.py", '''    return text.lstrip("#")
''', '''    return text.removeprefix("#")
''')]
OA_BYTES_EMPTY = [("records.py", '''    raw = fields.get("bytes") or "0"
''', '''    raw = fields.get("bytes", "0")
''')]
OA_FUTURE_FLOOR = [("stamp.py", '''    return -(-ahead // DAY)
''', '''    return ahead // DAY
''')]
OA_DOMAIN_FIRST = [("records.py", '''    local, at, domain = user.rpartition("@")
''', '''    domain, at, local = user.partition("@")
''')]
OA_MASK_SHORT = [("maskers.py", '''    return length // 4
''', '''    return length // 4 if length >= 8 else 0
''')]
OA_STRIP_ANYWHERE = [("names.py", '''    return fold(name).removeprefix(PREFIX)
''', '''    return fold(name).replace(PREFIX, "")
''')]
OA_FUTURE_PURGE = [("store.py", '''            if stamp.older_than(now, record.when, days):
                removed.append(record.id)
            else:
                keep.append(record)
''', '''            if stamp.older_than(now, record.when, days) or record.when > now:
                removed.append(record.id)
            else:
                keep.append(record)
''')]
OA_LEVEL_ALPHA = [("reports.py", '''    for level, count in sorted(counts.items(), key=lambda row: (level_rank(row[0]), row[0])):
''', '''    for level, count in sorted(counts.items()):
''')]
OA_PRUNE_ORDER = [("cmds.py", '''            len(removed), ", ".join(str(r) for r in removed), kept))
''', '''            len(removed), ", ".join(str(r) for r in sorted(removed, reverse=True)), kept))
''')]
# Weakened check: the self-check is turned off.
OA_NO_CHECK = [("invariant.py", '''def check(world):
    store = world.store
''', '''def check(world):
    return
    store = world.store
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
        # (d) everything fixed except the share formatting and the temporary policy copy
        "d_partial": with_defects("M08_temp_policy", "M09_share_format"),
        # (e) every fix applied, plus changes of documented behaviour
        "e_overaggressive": flat(OA_AGE_EXACT, OA_WINDOW_INCLUSIVE, OA_AVERAGE_HALF_UP),
        "e2_overaggressive_ids": flat(OA_CLEAN_ID, OA_BYTES_EMPTY, OA_FUTURE_FLOOR, OA_DOMAIN_FIRST),
        "e3_overaggressive_names": flat(OA_MASK_SHORT, OA_STRIP_ANYWHERE, OA_FUTURE_PURGE),
        "e4_overaggressive_tables": flat(OA_LEVEL_ALPHA, OA_PRUNE_ORDER),
        # (g) the self-check silenced, slips left in
        "g_check_disabled": flat(*DEFECTS.values(), OA_NO_CHECK),
    }
    for name, edits in trees.items():
        make_tree(os.path.join(ct, name, "patch"), edits)
    print("public/src, %d mutants and %d control trees written" % (len(DEFECTS), len(trees)))


if __name__ == "__main__":
    main()
