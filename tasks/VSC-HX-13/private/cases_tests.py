# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""ref_tests: ordinary behaviour (the original program passes all of them).
They avoid the defective paths but exercise the neighbouring code and the
deliberate exceptions (whole-block services, split-rate regions, the void
report, refunds for closed customers, ...)."""
import random

import gen_gold

SVC = {s[0]: s for s in gen_gold.SERVICES}
# services whose modules carry no defect, with block size and free allowance
CLEAN = [c for c in SVC if c not in ("sms", "queue")]


def allow_free(code):
    return SVC[code][7]


def usage_lines(cust, k, extra=3, codes=None):
    """usage lines that bill about K blocks (plus a partial block) for every clean ceil service"""
    out = []
    for code in (codes or CLEAN):
        _, _, unit, block, tiers, minc, mode, base = SVC[code]
        out.append("usage %s %s %d" % (cust, code, base + block * k + extra))
    return out


T = {}

T["t01_customer_basics"] = """customer add c-alpha team de EUR name="Alpha Works"
customer add c-beta free ca USD
customer add c-gamma starter jp JPY
set po c-alpha "PO 4411"
set email c-alpha ops@alpha.example
set phone c-alpha "+49 (30) 555-12"
set terms c-alpha 45
set note c-beta "first, trial"
set note c-beta -
set po c-alpha -
set name c-beta "Beta Ltd"
set region c-beta ny
set currency c-beta EUR
set currency c-beta KWD
set exempt c-gamma yes
set exempt c-gamma yes
customer show c-alpha
customer show c-beta
customer show c-gamma
customer list
customer list plan=team
customer list region=jp
customer list status=closed
customer history c-alpha
set terms c-alpha 0
set email c-alpha nobody
set currency c-alpha XXX
set region c-alpha atlantis
set phone c-alpha abc
customer show c-nobody
customer add Bad_Id team de EUR
audit 20
"""

T["t02_first_invoice_proration"] = """customer add c-p0 team de EUR
tick 10
customer add c-p10 team de EUR
tick 19
customer add c-p29 team de EUR
tick 1
customer add c-p30 team de EUR
tick 1
usage c-p30 requests 160000
usage c-p0 requests 160000 day=5
tick 30
invoice run 0
invoice run
invoice list
invoice show INV-0001
invoice show INV-0002
invoice show INV-0003
invoice show INV-0004
invoice show INV-0005
invoice show INV-0007
invoice run
invoice run 1
invoice run 2
invoice run 9
"""

lines = ["customer add c-rate free tx USD", "customer add c-rate2 free tx USD",
         "customer add c-rate3 enterprise tx USD"]
lines += usage_lines("c-rate", 130, 3)
lines += usage_lines("c-rate2", 7, 1)
lines += usage_lines("c-rate3", 400, 5)
lines += ["tick 30", "invoice run", "invoice show INV-0001", "invoice show INV-0002",
          "invoice show INV-0003", "usage summary c-rate 0"]
T["t03_usage_rating_basic"] = "\n".join(lines) + "\n"

T["t04_whole_mode_services"] = """customer add c-w free tx USD
customer add c-w2 starter tx USD
usage c-w voice 23
usage c-w ocr 95
usage c-w geocode 850
usage c-w voice 2
usage c-w2 voice 4
usage c-w2 ocr 9
usage c-w2 geocode 1000 day=0
usage c-w2 geocode 1000 day=0
quote c-w voice 23
quote c-w ocr 95
quote c-w geocode 850
quote c-w voice 4
quote c-w2 geocode 4000
tick 30
invoice run
invoice show INV-0001
invoice show INV-0002
service show voice
service show geocode
"""

T["t05_tier_boundaries"] = """customer add c-t free tx USD
quote c-t storage 102000
quote c-t storage 102001
quote c-t storage 402000
quote c-t storage 402001
quote c-t egress 520
quote c-t egress 521
quote c-t egress 2020
quote c-t egress 2021
quote c-t compute 1320
quote c-t compute 1321
quote c-t compute 1
quote c-t compute 121
quote c-t dns 100
quote c-t dns 10100
quote c-t cache 257
quote c-t cache 4000
customer add c-t2 team tx USD
quote c-t2 storage 124000
quote c-t2 storage 124001
usage c-t backup 30500
usage c-t backup 130500
tick 30
invoice run
invoice show INV-0001
"""

T["t06_coupon_kinds"] = """customer add c-k1 team tx USD
customer add c-k2 team tx USD
customer add c-k3 team tx USD
customer add c-k4 team tx USD
customer add c-k5 team tx USD
customer add c-k6 team tx USD
customer add c-k7 team tx USD
customer add c-k8 starter tx USD
customer add c-k9 team tx EUR
coupon add c-k1 pct_all 10
coupon add c-k2 pct_fee 25
coupon add c-k3 pct_usage 50
coupon add c-k4 fixed_all 12.50
coupon add c-k5 fixed_fee 5.00
coupon add c-k6 fixed_usage 4.00
coupon add c-k7 first_periods 20
coupon add c-k8 volume 20
coupon add c-k9 fixed_all 200.00
coupon add c-k9 pct_all 100
coupon add c-k1 pct_all 101
coupon add c-k1 pct_all 0
coupon add c-k1 fixed_all 0
coupon add c-k1 nonsense 5
coupon add c-k1 fixed_all 1.234
usage c-k1 requests 160000
usage c-k2 requests 160000
usage c-k3 requests 160000
usage c-k4 requests 160000
usage c-k5 requests 160000
usage c-k6 requests 160000
usage c-k7 requests 160000
usage c-k8 egress 5000
usage c-k9 requests 160000
coupon list c-k1
coupon kinds
tick 30
invoice run
invoice show INV-0001
invoice show INV-0002
invoice show INV-0003
invoice show INV-0004
invoice show INV-0005
invoice show INV-0006
invoice show INV-0007
invoice show INV-0008
invoice show INV-0009
"""

T["t07_coupon_until_n"] = """customer add c-u team tx USD
customer add c-u2 team tx USD
coupon add c-u pct_all 10 until=29
coupon add c-u first_periods 20 n=2
coupon add c-u fixed_all 1.00 until=60
coupon add c-u2 pct_fee 50 n=5
coupon list c-u
tick 100
usage c-u requests 160000 day=5
usage c-u requests 160000 day=35
usage c-u requests 160000 day=65
usage c-u2 requests 160000 day=5
invoice run 0
invoice run 1
coupon list c-u
coupon rm c-u 3
coupon rm c-u 9
coupon list c-u
invoice run 2
invoice show INV-0001
invoice show INV-0003
invoice show INV-0004
coupon rm c-u 1
coupon list c-u
coupon list c-u2
"""

lines = []
regions = ["ca", "ny", "tx", "wa", "de", "uk", "jp", "on", "ch"]
for r in regions:
    lines.append("customer add c-%s starter %s USD" % (r, r))
for r in regions:
    lines.append("usage c-%s egress 400" % r)
lines += ["coupon add c-ny pct_all 10", "coupon add c-wa fixed_all 2.00", "coupon add c-jp pct_usage 50",
          "coupon add c-ch pct_fee 30", "tick 31", "invoice run"]
for i in range(1, len(regions) + 1):
    lines.append("invoice show INV-%04d" % i)
lines += ["region list", "region show ny", "region show wa", "region show jp"]
T["t08_tax_regions"] = "\n".join(lines) + "\n"

T["t09_tax_exempt"] = """customer add c-e1 starter ca USD
customer add c-e2 starter de EUR
customer add c-e3 starter uk GBP
customer add c-e4 starter ny USD
customer add c-e5 starter ch USD
set exempt c-e1 yes
set exempt c-e2 yes
set exempt c-e4 yes
set exempt c-e5 yes
usage c-e1 egress 300
usage c-e2 egress 300
usage c-e3 egress 300
usage c-e4 egress 300
usage c-e5 egress 300
tick 30
invoice run
set exempt c-e2 no
set exempt c-e3 yes
usage c-e1 egress 300 day=30
usage c-e2 egress 300 day=30
usage c-e3 egress 300 day=30
tick 30
invoice run
invoice list
invoice show INV-0001
invoice show INV-0002
invoice show INV-0003
invoice show INV-0004
invoice show INV-0005
invoice show INV-0006
invoice show INV-0007
invoice show INV-0008
report tax_period
"""

lines = []
cur_list = ["EUR", "USD", "GBP", "JPY", "KWD", "CAD", "INR"]
for c in cur_list:
    lines.append("customer add c-%s starter de %s" % (c.lower(), c))
for c in cur_list:
    lines.append("usage c-%s egress 333" % c.lower())
    lines.append("usage c-%s logs 7777" % c.lower())
lines += ["tick 30", "invoice run"]
for i in range(1, 8):
    lines.append("invoice show INV-%04d" % i)
lines += ["pay c-jpy 1000", "pay c-kwd 1.250", "pay c-jpy 10.5", "pay c-kwd 1.2345", "pay c-inr 100",
          "pay c-eur 0.01", "pay c-usd 12", "credit add c-gbp 5.55", "credit add c-jpy 77",
          "statement c-jpy", "statement c-kwd", "ledger", "currency list"]
T["t10_currencies"] = "\n".join(lines) + "\n"

T["t11_payment_order"] = """customer add c-ord starter tx USD
customer add c-tie starter tx USD
usage c-ord egress 400
usage c-tie egress 400
set terms c-ord 90
set terms c-tie 60
tick 31
invoice run
usage c-ord egress 400
usage c-tie egress 400
set terms c-ord 20
set terms c-tie 30
tick 30
invoice run
usage c-ord egress 400
set terms c-ord 5
tick 30
invoice run
invoice list
pay c-ord 50
statement c-ord
pay c-ord 40
statement c-ord
pay c-tie 40
statement c-tie
pay c-tie 5
statement c-tie
pay c-ord 500
statement c-ord
"""

T["t12_pay_direct_overpay"] = """customer add c-d1 starter de EUR
customer add c-d2 starter de EUR
usage c-d1 egress 400
usage c-d2 egress 400
tick 30
invoice run
pay c-d1 5 inv=INV-0002
pay c-d1 5 inv=INV-0009
pay c-d1 999 inv=INV-0001
pay c-d1 10 inv=INV-0001
statement c-d1
pay c-d1 100.00 inv=INV-0001
pay c-d1 24.47 inv=INV-0001
pay c-d1 0.01 inv=INV-0001
pay c-d1 10.50
statement c-d1
void INV-0002
pay c-d2 1 inv=INV-0002
pay c-d2 1
statement c-d2
"""

T["t13_credit_flow"] = """customer add c-cr starter tx USD
customer add c-cr2 starter tx USD
credit add c-cr 50
credit add c-cr 0
credit add c-cr 1.234
usage c-cr egress 400
usage c-cr2 egress 400
credit add c-cr2 10
tick 31
invoice run
statement c-cr
statement c-cr2
usage c-cr egress 400
tick 30
invoice run
statement c-cr
credit add c-cr 100
pay c-cr2 100
statement c-cr2
customer show c-cr2
customer close c-cr
customer show c-cr
ledger c-cr
ledger c-cr2 kind=credit_in
report credits
"""

T["t14_refund_basic"] = """customer add c-rf starter de EUR
customer add c-rf2 starter ca USD
usage c-rf egress 400
usage c-rf2 egress 400
tick 30
invoice run
pay c-rf 40
pay c-rf2 10
refund INV-0001 5.25
statement c-rf
refund INV-0001 100
refund INV-0002 10.01
refund INV-0002 abc
refund INV-0009 1
refund INV-0002 0
invoice show INV-0001
pay c-rf 100
refund INV-0001 20
pay c-rf2 3.77
customer close c-rf2
refund INV-0002 3
refund INV-0002 7
customer close c-rf2
statement c-rf2
report out_customer
tick 40
dun
invoice show INV-0002
ledger kind=refund
"""

T["t15_void_rules"] = """customer add c-v1 starter de EUR
customer add c-v2 starter de EUR
usage c-v1 egress 400
usage c-v2 egress 400
tick 30
invoice run
pay c-v2 5
void INV-0002
void INV-0001
void INV-0001
void INV-0007
usage c-v1 requests 99000 day=7
usage c-v1 requests 99000 day=7 id=again
invoice list
invoice list state=void
invoice run 0
invoice list c-v1
statement c-v1
report voided
report voided cust=c-v1
report rev_region
report out_customer
invoice list state=paid
invoice list period=0
invoice list state=bogus
"""

T["t16_dunning_basic"] = """customer add c-l1 starter de EUR
customer add c-l2 business de EUR
customer add c-l3 starter uk GBP
set terms c-l3 10
usage c-l1 egress 400
usage c-l2 storage 900000
usage c-l2 egress 6000
usage c-l3 egress 400
tick 30
invoice run
invoice list
tick 5
dun
tick 40
dun
dun
invoice show INV-0001
invoice show INV-0002
invoice show INV-0003
pay c-l1 20
tick 1
dun
pay c-l1 100
tick 60
dun
invoice list
report late_customer
report late_customer cur=EUR
ledger kind=late
"""

lines = ["customer add c-g%d starter tx USD" % i for i in range(9)]
terms = [120, 115, 90, 89, 60, 59, 30, 29, 100]
for i, t in enumerate(terms):
    lines.append("set terms c-g%d %d" % (i, t))
for i in range(9):
    lines.append("usage c-g%d egress 400" % i)
lines += ["tick 30", "invoice run", "pay c-g8 500", "tick 120", "report aging", "report aging cur=USD",
          "report aging cust=c-g0", "report aging cur=EUR", "report aging cust=c-nobody"]
T["t17_aging_buckets"] = "\n".join(lines) + "\n"

T["t18_reports_grouped"] = """customer add c-a1 business de EUR
customer add c-a2 starter ca USD
customer add c-a3 team uk GBP
customer add c-a4 starter jp JPY
customer add c-a5 free tx USD
coupon add c-a1 pct_all 10
coupon add c-a3 fixed_all 5
usage c-a1 storage 150000 day=0
usage c-a2 egress 500
usage c-a3 compute 3000
usage c-a4 ocr 300
usage c-a5 logs 9000
tick 31
invoice run
usage c-a1 storage 150000
usage c-a2 egress 900
pay c-a1 100
pay c-a2 10
tick 40
dun
tick 20
invoice run 1
invoice run
pay c-a3 20
report list
report rev_region
report rev_region cur=USD
report rev_plan
report rev_period
report rev_period cust=c-a1
report tax_region
report tax_period
report disc_region
report late_customer
report out_customer
report out_customer cur=EUR
report credits
report payments
report payments cust=c-a2
report usage_units
report aging
report tax_region cur=XXX
report tax_region cust=c-zzz
report tax_region bogus=1
report nonsense
"""

T["t19_top_ranking"] = """customer add c-z1 starter tx USD
customer add c-z2 starter tx USD
customer add c-z3 starter tx USD
customer add c-y1 team tx USD
customer add c-x1 starter de EUR
customer add c-x2 free de EUR
usage c-z1 egress 400
usage c-z2 egress 400
usage c-z3 egress 400
usage c-y1 egress 100
usage c-x1 egress 400
usage c-x2 logs 9000
tick 30
invoice run
report top USD
report top USD 2
report top USD 1
report top EUR 10
report top GBP
report top XXX
report top USD 0
report top USD 200
coupon add c-z2 pct_all 10
usage c-z2 egress 400
usage c-z3 egress 800
tick 30
invoice run
report top USD 4
"""

T["t20_closed_customer"] = """customer add c-c1 starter de EUR
customer add c-c2 starter de EUR
customer add c-c3 starter de EUR
coupon add c-c3 pct_all 5
usage c-c1 egress 400
usage c-c2 egress 400
customer close c-c3
customer close c-c3
customer close c-c2
tick 30
invoice run
pay c-c1 100
customer close c-c1
usage c-c3 egress 10
usage c-c1 egress 10
usage batch c-c3 egress 10 20
plan set c-c3 team
coupon add c-c3 pct_all 5
coupon rm c-c3 1
credit add c-c3 5
pay c-c3 5
pay c-c1 5
set po c-c3 X1
set terms c-c3 10
set name c-c3 Foo
set region c-c3 ny
set exempt c-c3 yes
set note c-c3 hello
set email c-c3 a@b.c
set currency c-c3 USD
customer show c-c3
coupon list c-c3
usage list c-c3
statement c-c3
statement c-c1
customer list status=closed
customer list status=active
tick 30
invoice run
invoice list
refund INV-0001 5
customer history c-c3
report out_customer
"""

T["t21_usage_validation"] = """customer add c-q1 starter de EUR
tick 10
customer add c-q2 starter de EUR
usage c-q1 egress 5 day=11
usage c-q1 egress 5 day=x
usage c-q2 egress 5 day=3
usage c-q2 egress 5 day=10
usage c-q1 egress 5 day=0
usage c-q1 egress 5 id=a,b
usage c-q1 egress 5 id=ok-1
usage c-q1 egress 5 id=ok-1
usage c-q1 logs 5 id=ok-1
usage c-q2 egress 5 id=ok-1
usage c-q1 egress 1000001
usage c-q1 egress 12abc
usage c-q1 egress -4
usage c-q1 egress
usage c-q1 egress 5 colour=red
usage c-q1 egress 5 day=1 day=2
usage c-q1 nothing 5
usage nobody egress 5
tick 25
invoice run
usage c-q1 egress 5 day=2
usage c-q1 egress 5 day=33
usage c-q1 egress 5 day=35
usage c-q2 egress 5 day=11
void INV-0001
usage c-q1 egress 5 day=2
usage list c-q1
usage list c-q1 logs
usage summary c-q1 0
usage summary c-q1
usage summary c-q1 7
"""

T["t22_batch_single_customer"] = """customer add c-b1 starter de EUR
customer add c-b2 starter de EUR
usage batch c-b1 egress 100 200 300 id=run1
usage batch c-b1 egress 100 200 id=run1
usage batch c-b1 egress 50 id=run1x
usage batch c-b2 egress 100 200 id=other
usage batch c-b1 egress
usage batch c-b1 egress 10 0
usage batch c-b1 egress 10 x
usage batch c-b1 nothing 10
usage batch c-b1 egress 7 8 day=99
usage batch c-b1 egress 7 8 day=0 id=a,b
usage batch c-b2 logs 10 20 30
usage batch c-b2 logs 10 20 30
usage list c-b1
usage list c-b2
tick 30
invoice run
invoice show INV-0001
invoice show INV-0002
usage batch c-b1 egress 5 day=3
"""

T["t23_export_formats"] = """customer add c-ex1 team de EUR name="Ex, One & Co"
customer add c-ex2 free ca USD name="The ""Quoted"" Ltd"
set po c-ex1 "PO, 12"
set email c-ex1 bill@ex.example
set note c-ex2 "line one"
usage c-ex1 requests 160000 id=u1
usage c-ex2 logs 9000
tick 30
invoice run
pay c-ex1 20
refund INV-0001 1.5
export invoices csv
export invoices tsv
export ledger csv
export ledger tsv
export audit csv
export audit tsv
export customers csv
export customers tsv
export usage csv
export usage tsv
export nothing csv
export invoices xml
export invoices
"""

T["t24_audit_ledger_statement"] = """customer add c-s1 starter de EUR
customer add c-s2 starter de EUR
usage c-s1 egress 400
usage c-s2 egress 400
tick 30
invoice run
usage c-s1 egress 400
pay c-s1 10
pay c-s2 10
tick 31
invoice run
pay c-s1 5
refund INV-0001 2
credit add c-s2 7
audit
audit 3
audit 3 action=pay
audit 50 subject=c-s1
audit 0
audit x
ledger
ledger c-s1
ledger c-s1 kind=payment
ledger kind=invoice
ledger c-nobody
statement c-s1
statement c-s1 period=1
statement c-s2 period=0
statement c-s2 period=x
"""

T["t25_catalog"] = """help
help usage
help report
help nothing
plan list
plan show free
plan show enterprise
plan show nothing
service list
service show storage
service show queue
service show sms
service show nothing
region list
region show es
region show fr
region show nothing
currency list
coupon kinds
report list
customer add c-cat starter de EUR
customer add c-cat2 enterprise ch CHF
advise c-cat storage 50000
advise c-cat logs 100
advise c-cat2 egress 9000
quote c-cat storage 50000
quote c-cat2 backup 500000
quote c-cat requests 1
quote c-cat nothing 5
quote c-nobody storage 5
advise c-cat storage 0
today
tick 0
tick 401
tick 7
today
"""


def big_script():
    rnd = random.Random(1313)
    regions = ["ca", "ny", "tx", "wa", "de", "uk", "jp", "on", "ch"]
    curs = ["EUR", "USD", "GBP", "JPY", "KWD", "CAD", "INR"]
    plans = ["free", "starter", "team", "business", "enterprise"]
    services = [c for c in CLEAN]
    kinds = ["pct_all", "pct_fee", "pct_usage", "fixed_all", "fixed_usage", "first_periods", "volume"]
    out = []
    ids = ["c-%02d" % i for i in range(1, 25)]
    terms = {}
    due_days = set()
    day = 0
    for cid in ids:
        out.append("customer add %s %s %s %s" % (cid, rnd.choice(plans), rnd.choice(regions),
                                                rnd.choice(curs)))
        terms[cid] = 30
    invoices = 0
    prefix = 0
    closed = set()
    for step in range(520):
        r = rnd.random()
        cid = rnd.choice(ids)
        if cid in closed and r < 0.85:
            continue
        if r < 0.50:
            code = rnd.choice(services)
            block, base = SVC[code][3], SVC[code][7]
            units = rnd.randint(1, 5) * block + rnd.choice([0, 1, base, base + 7, base * 2])
            units = max(1, min(units, 900000))
            d = rnd.randint(max(0, day - 29 - day % 30), day)
            if rnd.random() < 0.15:
                prefix += 1
                out.append("usage batch %s %s %d %d %d day=%d id=bt%d" % (
                    cid, code, units, units // 2 + 1, units // 3 + 1, d, prefix))
            else:
                out.append("usage %s %s %d day=%d" % (cid, code, units, d))
        elif r < 0.56:
            out.append("coupon add %s %s %d" % (cid, rnd.choice(kinds), rnd.randint(1, 30))
                       if rnd.random() < 0.6 else "coupon add %s fixed_all %d.%02d" % (
                           cid, rnd.randint(1, 8), rnd.randint(0, 99)))
        elif r < 0.62:
            out.append("set terms %s %d" % (cid, rnd.choice([10, 14, 30, 45])))
            terms[cid] = int(out[-1].split()[3])
        elif r < 0.66:
            out.append("set exempt %s %s" % (cid, rnd.choice(["yes", "no"])))
        elif r < 0.70:
            adv = rnd.choice([3, 7, 12, 29, 31])
            day += adv
            out.append("tick %d" % adv)
        elif r < 0.78:
            p = max(0, day // 30 - 1)
            for c2 in ids:
                due_days.add(day + terms[c2])
            out.append("invoice run %d" % (rnd.randint(0, p) if day >= 30 else 0) if day >= 30 else "invoice run")
        elif r < 0.86:
            out.append("pay %s %d.%02d" % (cid, rnd.randint(1, 60), rnd.randint(0, 99)))
        elif r < 0.89:
            invoices += 1
            out.append("refund INV-%04d %d.%02d" % (rnd.randint(1, 30), 0, rnd.randint(1, 20)))
        elif r < 0.91:
            out.append("void INV-%04d" % rnd.randint(1, 30))
        elif r < 0.93:
            out.append("credit add %s %d" % (cid, rnd.randint(1, 20)))
        elif r < 0.95:
            if day not in due_days:
                out.append("dun")
        elif r < 0.96 and len(closed) < 3:
            out.append("customer close %s" % cid)
            closed.add(cid)
        elif r < 0.98:
            out.append(rnd.choice(["report rev_region", "report out_customer", "report aging",
                                   "report rev_plan", "report credits", "report late_customer",
                                   "report tax_period", "report usage_units", "report top USD 3",
                                   "report top EUR 3", "report disc_region", "report payments"]))
        else:
            out.append(rnd.choice(["statement %s" % cid, "customer show %s" % cid,
                                   "usage summary %s" % cid, "invoice list %s" % cid]))
    out += ["tick 30", "invoice run", "report rev_period", "report aging", "export invoices csv",
            "ledger kind=refund", "audit 5"]
    return "\n".join(out) + "\n"


T["t26_big_script"] = big_script()
