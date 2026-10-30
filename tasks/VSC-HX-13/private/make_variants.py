#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Derive public/src (the original program with all K=12 defects), the
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

D01_SMS_BLOCKS = [("svc_sms.py", '''    return money.ceil_div(billable, BLOCK)
''', '''    return billable // BLOCK
''')]

D02_QUEUE_TIER = [("svc_queue.py", '''        top = blocks if upto is None else min(blocks, upto)
''', '''        top = blocks if upto is None else min(blocks, upto - 1)
''')]

D03_ES_EXEMPT = [("tax_es.py", '''def compute(lines, discount, exempt):
    if exempt:
        return 0
    base = taxable_sum(lines) - discount
''', '''def compute(lines, discount, exempt):
    base = taxable_sum(lines) - discount
''')]

D04_FR_ROUNDING = [("tax_fr.py", '''    return money.pct(base, RATE_BP)
''', '''    return base * RATE_BP // 10000
''')]

D05_FIXED_FEE_CAP = [("disc_fixed_fee.py", '''    return min(cp.value, ctx.fee)
''', '''    return min(cp.value, ctx.subtotal)
''')]

D06_CHF_ROUNDING = [("cur_chf.py", '''    return (cents * RATE_PPM + 500000) // 1000000
''', '''    return int(round(cents * RATE_PPM / 1000000))
''')]

D07_PHONE_CLOSED = [("set_phone.py", '''    cust = customers.open(w, cmd.arg(0))
''', '''    cust = customers.get(w, cmd.arg(0))
''')]

D08_DUN_BOUNDARY = [("dunning.py", '''        if not timeutil.is_overdue(w.day, inv.due):
''', '''        if w.day < inv.due:
''')]

D09_PLAN_DAYS = [("planchange.py", '''    days = proration.days_left(w.day)
''', '''    days = timeutil.end(timeutil.period_of(w.day)) - w.day
''')]

D10_REFUND_CAP = [("refunds.py", '''    if amount > inv.paid - inv.refunded:
''', '''    if amount > inv.paid:
''')]

D11_TAX_REPORT_VOID = [("rpt_tax_region.py", '''    for inv in invoice.live(w):
''', '''    for inv in w.invoices.values():
''')]

D12_BATCH_KEY = [("usagebatch.py", '''            k = usage.key(cust.id, svc, rid)
''', '''            k = (svc, rid)
''')]

DEFECTS = {
    "M01_sms_blocks": D01_SMS_BLOCKS,
    "M02_queue_tier": D02_QUEUE_TIER,
    "M03_es_exempt": D03_ES_EXEMPT,
    "M04_fr_rounding": D04_FR_ROUNDING,
    "M05_fixed_fee_cap": D05_FIXED_FEE_CAP,
    "M06_chf_rounding": D06_CHF_ROUNDING,
    "M07_phone_closed": D07_PHONE_CLOSED,
    "M08_dun_boundary": D08_DUN_BOUNDARY,
    "M09_plan_days": D09_PLAN_DAYS,
    "M10_refund_cap": D10_REFUND_CAP,
    "M11_tax_report_void": D11_TAX_REPORT_VOID,
    "M12_batch_key": D12_BATCH_KEY,
}

# ---------------------------------------------------------------- control-only edits
# Over-aggressive "hardening" of deliberate exceptions:
OA_WHOLE_MODES = [
    ("svc_voice.py", "    return billable // BLOCK\n", "    return money.ceil_div(billable, BLOCK)\n"),
    ("svc_ocr.py", "    return billable // BLOCK\n", "    return money.ceil_div(billable, BLOCK)\n"),
    ("svc_geocode.py", "    return billable // BLOCK\n", "    return money.ceil_div(billable, BLOCK)\n"),
]
OA_SPLIT_TAX = [
    ("tax_ny.py", "    return money.pct(base, PARTS[0]) + money.pct(base, PARTS[1])\n",
     "    return money.pct(base, RATE_BP)\n"),
    ("tax_wa.py", "    return money.pct(base, PARTS[0]) + money.pct(base, PARTS[1])\n",
     "    return money.pct(base, RATE_BP)\n"),
]
OA_VOIDED_REPORT = [("rpt_voided.py", "    for inv in w.invoices.values():\n", "    for inv in invoice.live(w):\n"),
                    ("rpt_voided.py", "import currencies\n", "import currencies\nimport invoice\n")]
OA_CLOSED_READS = [
    ("refunds.py", "    inv = invoice.find(w, cmd.arg(0))\n    cur = currencies.get(inv.currency)\n",
     "    inv = invoice.find(w, cmd.arg(0))\n    customers.open(w, inv.cust)\n    cur = currencies.get(inv.currency)\n"),
    ("refunds.py", "import currencies\n", "import currencies\nimport customers\n"),
    ("statements.py", "    cust = customers.get(w, cmd.arg(0))\n    want",
     "    cust = customers.open(w, cmd.arg(0))\n    want"),
]
OA_LATE_TAXED = [
    ("dunning.py", "        inv.late += fee\n        inv.total += fee\n",
     "        inv.late += fee\n        inv.total += fee + money.pct(fee, 1000)\n"),
]
# Harmonising the overdue test towards the inline form of the defective site:
# the shared helper is changed (every other defect fixed as in gold).
MINORITY_OVERDUE = [("timeutil.py", "    return today > due\n", "    return today >= due\n")]
# A "fix" of the rounding mismatch by changing the shared pct helper (truncating everywhere).
MINORITY_PCT = [("money.py", "    return div_half_up(amount * bp, 10000)\n", "    return amount * bp // 10000\n")]

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
        # (d) everything fixed except the two subtlest variants
        "d_partial": with_defects("M05_fixed_fee_cap", "M06_chf_rounding"),
        # (e) every fix applied, plus "hardening" of deliberate exceptions
        "e_overaggressive": flat(OA_WHOLE_MODES, OA_SPLIT_TAX, OA_VOIDED_REPORT),
        "e2_overaggressive_closed": flat(OA_CLOSED_READS, OA_LATE_TAXED),
        # (g)/(h) inconsistencies resolved the wrong way
        "g_minority_overdue": flat(MINORITY_OVERDUE),
        "h_minority_pct": flat(MINORITY_PCT),
    }
    for name, edits in trees.items():
        make_tree(os.path.join(ct, name, "patch"), edits)
    print("public/src, %d mutants and %d control trees written" % (len(DEFECTS), len(trees)))


if __name__ == "__main__":
    main()
