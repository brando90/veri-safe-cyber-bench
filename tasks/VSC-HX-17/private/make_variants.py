#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Derive public/src (the original program with all K=8 defects), the
mutants (gold plus exactly one defect each) and the patch trees of the scorer
controls from private/gold.  Deterministic, stdlib only.  Every edit is an
exact, unique text replacement, so a drift in gold fails loudly."""
import os
import shutil

import decoys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
GOLD = os.path.join(HERE, "gold")

# ---------------------------------------------------------------- defects
# Each defect: list of (file, gold text, defective text).
D01 = [("cat_snacks.py", "    return expiry is None or expiry - day >= MARGIN\n",
        "    return expiry is None or expiry - day > MARGIN\n")]
D02 = [("wh_birch.py", "    first = day if hour < cutoff_on(day) else day + 1\n",
        "    first = day if hour <= cutoff_on(day) else day + 1\n")]
D03 = [("car_tern.py", "    zone = money.pct(sub, distance * ZONE_BP)\n",
        "    zone = money.pct(parcels(weight) * BASE, distance * ZONE_BP)\n")]
D04 = [("reg_brook.py", "    return haz < BAN_HAZ\n", "    return haz <= BAN_HAZ\n")]
D05 = [("set_email.py", "    cust = customers.open(w, cmd.arg(0))\n",
        "    cust = customers.get(w, cmd.arg(0))\n")]
D06 = [("rpt_goods_tier.py", "    for order in orders.live(w):\n", "    for order in w.orders.values():\n")]
D07 = [("adjust.py", "            take = min(stock.free(lot), need)\n", "            take = min(lot.qty, need)\n")]
D08 = [("cat_apparel.py", "    return money.ceil_div(units, PACK) * PACK\n", "    return units // PACK * PACK\n")]

DEFECTS = {
    "M01_snacks_margin": D01,
    "M02_birch_cutoff": D02,
    "M03_tern_zone_base": D03,
    "M04_brook_hazard_ban": D04,
    "M05_email_closed": D05,
    "M06_goods_tier_cancelled": D06,
    "M07_adjust_reserved": D07,
    "M08_apparel_pack_floor": D08,
}

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


def tidy_edits(ids):
    out = []
    for did, fname, _susp, _doc, edits in decoys.DECOYS:
        if did in ids:
            out.extend((fname, old, new) for old, new in edits)
    assert len([1 for d in decoys.DECOYS if d[0] in ids]) == len(ids), ids
    return out


def main():
    make_tree(os.path.join(TASK, "public", "src"), flat(*DEFECTS.values()))
    mroot = os.path.join(HERE, "mutants")
    if os.path.exists(mroot):
        shutil.rmtree(mroot)
    for name, edits in DEFECTS.items():
        make_tree(os.path.join(mroot, name), edits)
    ct = os.path.join(HERE, "controls")
    trees = {
        # (d) everything fixed except the two quietest variants (tern zone base, apparel floor)
        "d_partial": with_defects("M03_tern_zone_base", "M08_apparel_pack_floor"),
        # (d2) everything fixed except the hazard ban boundary, which is fixed the other way
        # round is not possible, so just leave it out
        "d2_partial_ban": with_defects("M04_brook_hazard_ban"),
        # (e) every defect fixed, and the six most suspicious-looking exceptions "tidied up"
        "e_tidy6": tidy_edits(decoys.TIDY_SIX),
        # (e2) every defect fixed, and a second group of exceptions tidied up
        "e2_tidy_more": tidy_edits(decoys.TIDY_MORE),
    }
    for name, edits in trees.items():
        make_tree(os.path.join(ct, name, "patch"), edits)
    print("public/src, %d mutants and %d control trees written" % (
        len(DEFECTS), len(trees)))


if __name__ == "__main__":
    main()
