#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Write every .in file (public/smoke, private/ref_tests, private/ref_edge).
Expected .out files are produced from gold by build_private.sh.
Deterministic: the one generated script uses a fixed seed."""
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)

# ---------------------------------------------------------------- smoke (ordinary behaviour only)
SMOKE = {
"s1_first_invoice": """# customers, usage and a first invoice
customer add c-acme team de EUR name="Acme GmbH"
customer add c-bolt starter ca USD
tick 12
customer add c-nova starter uk GBP
usage c-acme storage 40000 id=m1
usage c-acme egress 500
usage c-acme requests 90000
usage c-bolt egress 200 day=3
usage c-bolt compute 400
usage c-nova cdn 60
usage summary c-acme
tick 20
invoice run
invoice show INV-0001
invoice show INV-0002
invoice show INV-0003
invoice list
customer show c-acme
""",
"s2_rating_catalog": """# service catalogue, quotes and plan advice
service list
service show storage
plan show team
region show de
region list
currency list
customer add c-one free tx USD
quote c-one egress 300
quote c-one storage 9000
quote c-one logs 20000
advise c-one egress 600
usage c-one storage 9000
usage c-one egress 300
usage c-one cache 900
usage c-one dns 5000
tick 31
invoice run
invoice show INV-0001
""",
"s3_payments_refund_dun": """# payments, credit, a refund, a void and late fees
customer add c-pay starter de EUR
customer add c-two team uk GBP
set terms c-two 14
usage c-pay storage 30000
usage c-pay egress 400
usage c-two compute 900
tick 30
invoice run
pay c-pay 10
pay c-pay 15.50 inv=INV-0001
credit add c-two 20
refund INV-0001 5
statement c-pay
tick 40
dun
dun
invoice list state=open
pay c-two 50
void INV-0002
ledger c-pay
audit 6
""",
"s4_coupons_reports": """# coupons and reports
customer add c-a business de EUR
customer add c-b starter ca USD
customer add c-c team ny USD
coupon add c-a pct_all 10
coupon add c-b fixed_all 3.00
coupon add c-c pct_usage 25
coupon add c-c first_periods 5 n=1
coupon list c-c
tick 15
usage c-a storage 120000
usage c-a backup 90000
usage c-b egress 300
usage c-c search 500
usage c-c metrics 4000
tick 15
invoice run
report rev_region
report rev_plan
report tax_period
report disc_region
report out_customer
report top USD
tick 31
invoice run
report rev_period
report aging
report usage_units
""",
"s5_errors_exports": """# refused commands and exports
customer add c-x team de EUR
customer add c-x team de EUR
customer add c-y gold de EUR
customer add c-y team mars EUR
usage c-x storage 100
usage c-x teleport 5
usage c-x storage 0
usage c-x storage 10 day=40
pay c-x 0
pay c-x 5.555
frobnicate now
invoice run
tick 5
invoice show INV-0009
set terms c-x 400
set exempt c-x maybe
export invoices csv
export customers tsv
export ledger csv
export audit csv
help report
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
    for sub, table in (("public/smoke", SMOKE),):
        d = os.path.join(TASK, sub)
        os.makedirs(d, exist_ok=True)
        for name, text in table.items():
            with open(os.path.join(d, name + ".in"), "w") as f:
                f.write(text)
    for sub, table in (("private/ref_tests", REF_TESTS), ("private/ref_edge", REF_EDGE)):
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
