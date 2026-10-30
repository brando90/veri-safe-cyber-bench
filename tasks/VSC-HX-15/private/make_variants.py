#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Derive public/src (the original program with all K=9 defects), the mutants
(gold plus exactly one defect each) and the patch trees of the scorer controls
from private/gold.  Deterministic, stdlib only.  Every edit is an exact, unique
text replacement, so a drift in gold fails loudly."""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
GOLD = os.path.join(HERE, "gold")

# ---------------------------------------------------------------- defects
# Each defect: list of (file, gold text, defective text).

D1_CAP_ZERO = [("quota.py", '''        if limit and used >= limit:
''', '''        if used >= limit:
''')]

D2_HOLD_UNITS = [("alerts.py", '''    limit = world.ships.hold_minutes(ship, world.config) * 60
''', '''    limit = world.ships.hold_minutes(ship, world.config) * units.MIN_MS
'''), ("alerts.py", '''                             "dur=%ds limit=%ds" % (exc.duration, limit)))
''', '''                             "dur=%ds limit=%ds" % (exc.duration, limit // units.SEC_MS)))
''')]

D3_JOURNEY_END = [("sla.py", '''        rs = windows.select(rs, opened, closed + 1)
''', '''        rs = windows.select(rs, opened, closed)
''')]

D4_STOP_BASE = [("legs.py", '''        left = ship.arrival_at(i + 1)
        came = ship.arrival_at(i + 2)
''', '''        left = ship.arrival_at(i)
        came = ship.arrival_at(i + 1)
''')]

D5_SKEW_SIGN = [("ingest.py", '''calib.correct(units.parse_ms(opts["t"]), -ship.skew * units.SEC_MS)
''', '''calib.correct(units.parse_ms(opts["t"]), ship.skew * units.SEC_MS)
''')]

D6_LABEL_ESCAPE = [("export.py", '''"ship", ship.sid, tsvfmt.esc(ship.label), ship.route,''',
                    '''"ship", ship.sid, ship.label, ship.route,''')]

D7_TIE_PRECISION = [("ranking.py", '''        rows.append((sid, sla.percent_tenths(sc)))
    scored = [r for r in rows if r[1] is not None]
    scored.sort(key=lambda r: (r[1], textnorm.natural_key(r[0])))
    unscored = [r for r in rows if r[1] is None]
    return scored + unscored
''', '''        rows.append((sid, sla.percent_tenths(sc), sc))
    scored = [r for r in rows if r[1] is not None]
    scored.sort(key=lambda r: (r[2].inside / r[2].total, textnorm.natural_key(r[0])))
    unscored = [r for r in rows if r[1] is None]
    return [(r[0], r[1]) for r in scored + unscored]
''')]

D8_QUERY_CLEAN = [("cmd_views.py", '''    query = textnorm.clean_label(" ".join(pos))
''', '''    query = " ".join(pos)
''')]

D9_CLAMP_ORDER = [("ingest.py", '''    temp = calib.calibrate(units.parse_tenths(opts["temp"]), ship.offset)
''', '''    raw = units.parse_tenths(opts["temp"], calib.SENSOR_MIN, calib.SENSOR_MAX)
    temp = calib.calibrate(raw, ship.offset)
''')]

DEFECTS = {
    "M01_cap_zero": D1_CAP_ZERO,
    "M02_hold_units": D2_HOLD_UNITS,
    "M03_journey_end": D3_JOURNEY_END,
    "M04_stop_base": D4_STOP_BASE,
    "M05_skew_sign": D5_SKEW_SIGN,
    "M06_label_escape": D6_LABEL_ESCAPE,
    "M07_tie_precision": D7_TIE_PRECISION,
    "M08_query_clean": D8_QUERY_CLEAN,
    "M09_clamp_order": D9_CLAMP_ORDER,
}

# ---------------------------------------------------------------- control-only edits
# Over-aggressive "fixes" that change documented behaviour.
OA_CUTOFF_DROPS = [("readings.py", '''from bisect import bisect_left
''', '''from bisect import bisect_left, bisect_right
'''), ("readings.py", '''        i = bisect_left(rs, cutoff, key=_ts)
        del rs[:i]''', '''        i = bisect_right(rs, cutoff, key=_ts)
        del rs[:i]''')]
OA_RANGE_END = [("cmd_common.py", '''        end = units.parse_ms(opts["to"]) + 1
''', '''        end = units.parse_ms(opts["to"])
''')]
OA_STRIP_ALL = [("textnorm.py", '''    return BLANK_RUN.sub(" ", text).strip(" ")
''', '''    return " ".join(text.split())
''')]
OA_DELAY_FLOOR = [("schedule.py", '''    return int((actual - plan) / units.MIN_MS)
''', '''    return (actual - plan) // units.MIN_MS
''')]
OA_AVG_ROUND = [("rollup.py", '''        avg = units.div_round_half_up(sum(temps), len(temps))
''', '''        avg = round(sum(temps) / len(temps))
''')]

# Wrong-side fixes: the symptom of a defect is repaired in the module that owns the convention.
WS_CAP = [("shipments.py", '''        return cfg.get("cap") if ship.cap is None else ship.cap
''', '''        value = cfg.get("cap") if ship.cap is None else ship.cap
        return value if value else 1 << 30
''')]
WS_DURATION = [("excursions.py", '''        return (self.end - self.start) // units.SEC_MS
''', '''        return self.end - self.start
''')]
WS_WINDOW = [("windows.py", '''from bisect import bisect_left
''', '''from bisect import bisect_left, bisect_right
'''), ("windows.py", '''    last = bisect_left(rs, end, key=_ts)
''', '''    last = bisect_right(rs, end, key=_ts)
''')]
WS_STOP = [("shipments.py", '''        return self.arrivals.get(stop)
''', '''        return self.arrivals.get(stop + 1)
''')]
WS_CORRECT = [("calib.py", '''    moved = ts + offset
''', '''    moved = ts - offset
''')]
WS_ROW = [("tsvfmt.py", '''    return "\\t".join(str(f) for f in fields)
''', '''    return "\\t".join(esc(str(f)) for f in fields)
''')]

# Partial fix of the query defect: Unicode normalisation only, blank runs stay.
PARTIAL_NFC = [("cmd_views.py", '''    query = textnorm.clean_label(" ".join(pos))
''', '''    query = unicodedata.normalize("NFC", " ".join(pos))
'''), ("cmd_views.py", '''import alerts
''', '''import unicodedata

import alerts
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
        # (d) everything fixed except the two hardest variants
        "d_partial": with_defects("M07_tie_precision", "M09_clamp_order"),
        # (e) every fix applied, plus changes of documented behaviour
        "e_overaggressive": flat(OA_CUTOFF_DROPS, OA_RANGE_END, OA_STRIP_ALL, OA_DELAY_FLOOR,
                                 OA_AVG_ROUND),
        # (e2) six symptoms repaired on the contract side's other half; seven and nine fixed in gold
        "e2_wrong_side": flat(D1_CAP_ZERO, D2_HOLD_UNITS, D3_JOURNEY_END, D4_STOP_BASE,
                              D5_SKEW_SIGN, D6_LABEL_ESCAPE, WS_CAP, WS_DURATION, WS_WINDOW,
                              WS_STOP, WS_CORRECT, WS_ROW),
        # (p1) the query defect repaired for Unicode normalisation only
        "p1_find_nfc_only": PARTIAL_NFC,
    }
    for name, edits in trees.items():
        make_tree(os.path.join(ct, name, "patch"), edits)
    print("public/src, %d mutants and %d control trees written" % (len(DEFECTS), len(trees)))


if __name__ == "__main__":
    main()
