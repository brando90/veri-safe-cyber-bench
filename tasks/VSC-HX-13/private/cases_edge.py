# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""ref_edge: cases that fail on the original program and pass on gold.
Each exercises one defect (several of them for the sweeps)."""
import gen_gold

T = {}

T["e01_sms_partial_block"] = """customer add c-s1 free tx USD
customer add c-s2 starter ca USD
quote c-s1 sms 101
quote c-s1 sms 175
quote c-s1 sms 200
quote c-s1 sms 250
quote c-s1 sms 299
quote c-s2 sms 401
quote c-s2 sms 880
advise c-s2 sms 450
"""

T["e02_sms_invoice"] = """customer add c-s1 starter tx USD
customer add c-s2 team ny USD
usage c-s1 sms 60
usage c-s1 sms 470
usage c-s2 sms 20 day=0
usage c-s2 sms 1000
usage c-s2 egress 15
tick 30
invoice run
invoice show INV-0001
invoice show INV-0002
report usage_units
"""

T["e03_queue_tier_boundary"] = """customer add c-q free tx USD
quote c-q queue 1600
quote c-q queue 1601
quote c-q queue 1650
quote c-q queue 1651
quote c-q queue 6100
quote c-q queue 6101
quote c-q queue 7600
quote c-q queue 100
quote c-q queue 150
quote c-q queue 151
service show queue
"""

T["e04_queue_invoice"] = """customer add c-q1 free de EUR
customer add c-q2 business uk GBP
usage c-q1 queue 1500
usage c-q1 queue 100
usage c-q2 queue 6100
usage c-q2 queue 3000
usage c-q2 queue 500
tick 30
invoice run
invoice show INV-0001
invoice show INV-0002
report rev_period
report rev_plan
"""

T["e05_es_exempt_invoice"] = """customer add c-es starter es EUR
set exempt c-es yes
usage c-es egress 300
usage c-es logs 5000
tick 30
invoice run
invoice show INV-0001
"""

T["e06_es_exempt_toggle"] = """customer add c-e1 team es EUR
customer add c-e2 team es EUR
customer add c-e3 team es EUR
set exempt c-e1 yes
set exempt c-e3 yes
usage c-e1 requests 90000
usage c-e2 requests 90000
usage c-e3 requests 90000
coupon add c-e3 pct_all 10
tick 30
invoice run
set exempt c-e1 no
set exempt c-e2 yes
usage c-e1 requests 90000
usage c-e2 requests 90000
tick 30
invoice run
invoice list
invoice show INV-0003
invoice show INV-0004
report tax_period
"""

T["e07_fr_tax_half"] = """customer add c-f1 starter fr EUR
customer add c-f2 starter fr EUR
customer add c-f3 team fr USD
usage c-f2 egress 300
usage c-f3 requests 90000
tick 30
invoice run
invoice show INV-0001
invoice show INV-0002
invoice show INV-0003
"""

T["e08_fr_tax_discount_late"] = """customer add c-f1 business fr GBP
customer add c-f2 starter fr EUR
customer add c-f3 starter fr JPY
coupon add c-f1 pct_fee 7
coupon add c-f2 fixed_all 1.23
usage c-f1 storage 90000
usage c-f2 egress 77
usage c-f3 cdn 55
tick 30
invoice run
invoice show INV-0001
invoice show INV-0002
invoice show INV-0003
report tax_region
report tax_period
region show fr
"""

T["e09_fixed_fee_cap"] = """customer add c-x1 starter tx USD
customer add c-x2 starter tx USD
customer add c-x3 team de EUR
coupon add c-x1 fixed_fee 25.00
coupon add c-x2 fixed_fee 3.00
coupon add c-x3 fixed_fee 100.00
usage c-x1 egress 400
usage c-x2 egress 400
usage c-x3 storage 150000
tick 30
invoice run
invoice show INV-0001
invoice show INV-0002
invoice show INV-0003
report disc_region
"""

T["e10_fixed_kinds_caps"] = """customer add c-y1 starter ca USD
customer add c-y2 starter ca USD
customer add c-y3 starter ca USD
customer add c-y4 free ca USD
customer add c-y5 business ny USD
coupon add c-y1 fixed_all 500.00
coupon add c-y2 fixed_usage 500.00
coupon add c-y3 fixed_fee 500.00
coupon add c-y4 fixed_fee 40.00
coupon add c-y5 fixed_fee 150.00
coupon add c-y5 fixed_usage 2.00
usage c-y1 egress 300
usage c-y2 egress 300
usage c-y3 egress 300
usage c-y4 logs 9000
usage c-y5 compute 4000
tick 30
invoice run
invoice show INV-0001
invoice show INV-0002
invoice show INV-0003
invoice show INV-0004
invoice show INV-0005
coupon list c-y3
coupon list c-y5
"""

T["e11_chf_half_quote"] = """customer add c-ch1 starter ch CHF
customer add c-ch2 free ch CHF
quote c-ch1 requests 8000
quote c-ch1 requests 5000
quote c-ch1 requests 38000
quote c-ch1 logs 1750
quote c-ch1 logs 1500
quote c-ch2 requests 8000
quote c-ch2 cdn 25
quote c-ch2 egress 30
quote c-ch2 search 100
advise c-ch2 requests 20000
currency list
"""

T["e12_chf_invoice"] = """customer add c-ch1 team ch CHF
customer add c-ch2 starter on CHF
customer add c-ch3 free de CHF
usage c-ch1 requests 8000
usage c-ch1 requests 7000
usage c-ch1 logs 1750
usage c-ch2 requests 20000
usage c-ch2 cdn 40
usage c-ch3 requests 8000
usage c-ch3 logs 1250
tick 30
invoice run
invoice show INV-0001
invoice show INV-0002
invoice show INV-0003
pay c-ch3 1.00
statement c-ch3
"""

T["e13_phone_closed"] = """customer add c-p1 starter de EUR
customer add c-p2 starter de EUR
set phone c-p1 +49-30-1234
customer close c-p1
set phone c-p1 +49-30-9999
customer show c-p1
customer history c-p1
"""

T["e14_phone_closed_audit"] = """customer add c-p1 free ca USD
customer add c-p2 free ca USD
customer add c-p3 free ca USD
customer close c-p2
customer close c-p3
set phone c-p3 555-0101
set phone c-p2 555-0102
set phone c-p1 555-0103
set phone c-p1 555-0103
set note c-p3 hi
export customers csv
audit 10
audit 10 subject=c-p2
"""

T["e15_dun_due_day"] = """customer add c-d1 starter de EUR
customer add c-d2 starter de EUR
set terms c-d2 10
usage c-d1 egress 400
usage c-d2 egress 400
tick 30
invoice run
tick 10
dun
invoice show INV-0002
tick 20
dun
invoice show INV-0001
invoice show INV-0002
"""

T["e16_dun_day_after"] = """customer add c-d1 starter tx USD
customer add c-d2 business tx USD
set terms c-d1 15
set terms c-d2 45
usage c-d1 egress 400
usage c-d2 egress 400
tick 30
invoice run
tick 15
dun
tick 1
dun
tick 29
dun
tick 1
dun
invoice list
report late_customer
report aging
ledger kind=late
"""

T["e17_plan_change_mid"] = """customer add c-pc1 starter de EUR
customer add c-pc2 team ca USD
customer add c-pc3 business uk GBP
tick 10
plan set c-pc1 team
plan set c-pc2 starter
tick 15
plan set c-pc3 enterprise
tick 5
invoice run
invoice show INV-0001
invoice show INV-0002
invoice show INV-0003
customer history c-pc1
"""

T["e18_plan_change_edges"] = """customer add c-pc1 free tx USD
customer add c-pc2 starter tx USD
customer add c-pc3 team tx USD
plan set c-pc1 business
tick 29
plan set c-pc2 enterprise
tick 1
plan set c-pc3 business
tick 30
plan set c-pc1 free
plan set c-pc1 enterprise
tick 30
invoice run 0
invoice run 1
invoice show INV-0001
invoice show INV-0002
invoice show INV-0003
invoice show INV-0004
invoice show INV-0005
invoice show INV-0006
"""

T["e19_refund_twice"] = """customer add c-r1 starter de EUR
usage c-r1 egress 400
tick 30
invoice run
pay c-r1 30
refund INV-0001 20
refund INV-0001 20
statement c-r1
invoice show INV-0001
"""

T["e20_refund_boundary"] = """customer add c-r1 starter ca USD
customer add c-r2 starter ca USD
usage c-r1 egress 400
usage c-r2 egress 400
tick 30
invoice run
pay c-r1 100
pay c-r2 100
refund INV-0001 10
refund INV-0001 24.11
refund INV-0001 0.01
refund INV-0002 34.11
refund INV-0002 0.01
invoice show INV-0001
invoice show INV-0002
ledger kind=refund
statement c-r1
"""

T["e21_tax_report_after_void"] = """customer add c-t1 starter de EUR
customer add c-t2 starter de EUR
customer add c-t3 starter ca USD
usage c-t1 egress 400
usage c-t2 egress 400
usage c-t3 egress 400
tick 30
invoice run
report tax_region
void INV-0002
report tax_region
report rev_region
report tax_period
"""

T["e22_tax_report_filters"] = """customer add c-t1 team uk GBP
customer add c-t2 team uk GBP
customer add c-t3 starter tx USD
customer add c-t4 starter ny USD
usage c-t1 requests 90000
usage c-t2 requests 90000
usage c-t3 egress 100
usage c-t4 egress 100
tick 30
invoice run
void INV-0001
void INV-0003
report tax_region
report tax_region cur=GBP
report tax_region cur=USD
report tax_region cust=c-t2
report tax_region cust=c-t1
report tax_region cust=c-t3
invoice run 0
report tax_region
report voided
"""

T["e23_batch_same_prefix"] = """customer add c-b1 starter de EUR
customer add c-b2 starter de EUR
usage batch c-b1 egress 10 20 id=run
usage batch c-b2 egress 10 20 id=run
usage batch c-b1 egress 5 id=run
usage batch c-b2 logs 5 6 id=run
usage list c-b1
usage list c-b2
"""

T["e24_batch_vs_single"] = """customer add c-b1 starter de EUR
customer add c-b2 starter de EUR
usage c-b1 egress 5 id=m-1
usage batch c-b1 egress 1 2 id=m
usage c-b2 egress 5 id=m-2
usage batch c-b2 egress 1 2 3 id=m
usage batch c-b2 egress 1 id=n
usage c-b2 egress 4 id=n-1
usage list c-b1
usage list c-b2
"""


def sweep_quotes():
    out = ["customer add c-free free tx USD", "customer add c-biz business de EUR",
           "customer add c-ch starter ch CHF"]
    for s in gen_gold.SERVICES:
        code, block, base = s[0], s[3], s[7]
        for cust, mult in (("c-free", 1), ("c-biz", 40), ("c-ch", 4)):
            allow = base * mult
            for blocks in (1, 3, 10, 30, 31, 60, 100, 101, 120, 121, 200, 201):
                for extra in (0, 1):
                    out.append("quote %s %s %d" % (cust, code, allow + blocks * block - (block - 1 if extra else 0)))
    return "\n".join(out) + "\n"


T["e25_sweep_quotes"] = sweep_quotes()


def sweep_regions():
    out = []
    regions = [t[0] for t in gen_gold.TAXES]
    plans = ["starter", "team", "business"]
    n = 0
    for i, r in enumerate(regions):
        for j, plan in enumerate(plans):
            n += 1
            out.append("customer add c-%s%d %s %s %s" % (r, j, plan, r, ["EUR", "USD", "GBP"][(i + j) % 3]))
    for i, r in enumerate(regions):
        for j in range(3):
            out.append("usage c-%s%d egress %d" % (r, j, 47 + 31 * i + 17 * j))
            out.append("usage c-%s%d logs %d" % (r, j, 1000 + 333 * i + 250 * j))
        if i % 2 == 0:
            out.append("set exempt c-%s1 yes" % r)
    out += ["tick 30", "invoice run"]
    for k in range(1, n + 1):
        out.append("invoice show INV-%04d" % k)
    out += ["report tax_region", "report tax_period", "report rev_region"]
    return "\n".join(out) + "\n"


T["e26_sweep_regions"] = sweep_regions()


def sweep_currencies():
    out = []
    curs = [c[0] for c in gen_gold.CURRENCIES]
    plans = ["free", "starter", "team", "business"]
    k = 0
    for c in curs:
        for j in range(0, 30, 6):
            k += 1
            out.append("customer add c-%s%d %s ca %s" % (c.lower(), j, plans[(k + j) % 4], c))
    for c in curs:
        for j in range(0, 30, 6):
            out.append("usage c-%s%d requests %d" % (c.lower(), j, 5000 + 1000 * (1 + (j // 6) * 2)))
            out.append("usage c-%s%d cdn %d" % (c.lower(), j, 10 + 5 * (1 + j // 6)))
    out += ["tick 30", "invoice run"]
    for i in range(1, k + 1):
        out.append("invoice show INV-%04d" % i)
    return "\n".join(out) + "\n"


T["e27_sweep_currencies"] = sweep_currencies()
