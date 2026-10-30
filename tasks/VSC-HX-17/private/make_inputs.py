#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Write every .in file (public/smoke, private/ref_tests, private/ref_edge).
Expected .out files are produced from gold by build_private.sh.
Deterministic: the one generated script uses a fixed seed."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)

# ---------------------------------------------------------------- smoke (ordinary behaviour only)
SMOKE = {
"s1_first_orders": """# stock, two customers, orders and shipments
customer add c-acme delta tier=gold name="Acme Works"
customer add c-bolt arden
receive alder paper-a4 400
receive alder hammer-1 60
receive harbor paper-a4 200
receive dune milk-1l 120
stock alder
order add c-acme paper-a4:50 hammer-1:6
order show ORD-0001
order add c-bolt paper-a4:30
order add c-bolt milk-1l:24 ref=m-1
order list
tick 1
ship ORD-0001
ship ORD-0002 at=9
ship ORD-0003
order list state=shipped
customer show c-acme
""",
"s2_catalog_listings": """# reference data
sku list
sku show milk-1l
warehouse list
warehouse show alder
category list
category show dairy
carrier list
carrier show swift
region list
region show arden
tier list
help order
""",
"s3_cancel_return_backorder": """# a short order, a cancellation, a return and a backorder
customer add c-one brook
customer add c-two crest tier=silver
receive alder shirt-m 60
receive alder tumbler-6 24
order add c-one shirt-m:40 tumbler-6:12
order add c-two shirt-m:40
order show ORD-0002
order cancel ORD-0001
order show ORD-0001
backorder run
order show ORD-0002
ship ORD-0002
tick 3
return ORD-0002 shirt-m 5
return ORD-0002 shirt-m 2 cond=damaged
stock alder
ledger alder
""",
"s4_stock_operations": """# receipts, adjustments, transfers and expiry
customer add c-st arden
receive alder bolt-m6 1000
receive elm bolt-m6 500
receive dune yogurt-4 60
receive dune pizza-fr 40
receive fjord pizza-fr 16
adjust alder bolt-m6 -50
adjust elm bolt-m6 25
transfer alder harbor bolt-m6 300
transfer dune fjord yogurt-4 24
stock
order add c-st yogurt-4:20
tick 25
expire
replenish
ledger alder
audit 5
""",
"s5_reports_and_errors": """# reports and refused commands
customer add c-r1 forge
customer add c-r2 gale tier=gold
receive alder cable-usb 500
receive alder charger-20 100
receive larch plank-2m 200
order add c-r1 cable-usb:100 plank-2m:20
order add c-r2 cable-usb:80
ship ORD-0001
ship ORD-0002
report goods_region
report goods_customer
report freight_carrier
report duty_region
report stock_wh
report value_wh
report status
report low_stock
order add c-nobody cable-usb:1
order add c-r1 teleporter:1
order add c-r1 cable-usb:abc
ship ORD-0009
receive alder dairy 5
receive nowhere paper-a4 5
frobnicate now
export orders csv
export shipments tsv
""",
}

import cases_tests  # noqa: E402

REF_TESTS = cases_tests.T
try:
    import cases_edge  # noqa: E402
    REF_EDGE = cases_edge.T
except ImportError:
    REF_EDGE = {}


def write_all():
    for sub, table in (("public/smoke", SMOKE), ("private/ref_tests", REF_TESTS),
                       ("private/ref_edge", REF_EDGE)):
        d = os.path.join(TASK, sub)
        os.makedirs(d, exist_ok=True)
        for old in os.listdir(d):
            if old.endswith(".in") or old.endswith(".out"):
                os.remove(os.path.join(d, old))
        for name, text in table.items():
            with open(os.path.join(d, name + ".in"), "w") as f:
                f.write(text)
    print("inputs written: %d smoke, %d ref_tests, %d ref_edge" % (len(SMOKE), len(REF_TESTS), len(REF_EDGE)))


if __name__ == "__main__":
    write_all()
