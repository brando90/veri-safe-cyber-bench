#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Write every .in file (public/smoke, private/ref_tests, private/ref_edge).

Expected .out files are produced from gold by build_private.sh.  The long
streams are generated with fixed seeds; the generators drive the gold World
in-process only to pick sensible next commands (which accounts are open,
what they hold), so the streams are deterministic functions of gold."""
import io
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "gold"))
sys.dont_write_bytecode = True

import commands as g_commands  # noqa: E402
import invariant as g_invariant  # noqa: E402
import lexer as g_lexer  # noqa: E402
from errors import CommandError  # noqa: E402
from output import Output  # noqa: E402
from world import World  # noqa: E402

MIN = 60000
HOUR = 60 * MIN


class Driver:
    """Builds a script line by line while running it on gold."""

    def __init__(self):
        self.lines = []
        self.w = World(Output(io.StringIO()))

    def __call__(self, line):
        self.lines.append(line)
        try:
            cmd = g_lexer.parse(line)
            if cmd is not None:
                self.w.dispatch(cmd)
        except CommandError:
            pass
        g_invariant.quick(self.w)

    def many(self, lines):
        for line in lines:
            self(line)

    def acct(self, name):
        return self.w.accounts.by_name.get(name)

    @property
    def now(self):
        return self.w.clock.now

    @property
    def records(self):
        return self.w.journal.next_index

    def text(self):
        g_invariant.full(self.w)
        return "\n".join(self.lines) + "\n"


def lines(text):
    return [ln for ln in text.strip("\n").split("\n")]


# ====================================================================== smoke

SMOKE = {
"s1_accounts_and_money": """# open accounts, move money, look at balances
open alice
open bob overdraft=20
open carol daily=50
deposit alice 120.50
deposit bob 10
transfer alice bob 20.25
withdraw bob 35
withdraw bob 1
withdraw carol 5
transfer alice carol 7.5
balance alice
balance bob
accounts
history alice
show T0.2
journal
check
""",
"s2_holds": """# holds with and without a ttl
open shop
deposit shop 100
hold shop 30 ttl=10s
hold shop 50
hold shop 30
holds shop
balance shop
clock advance 5s
capture H001 amount=12 to=shop
capture H001 amount=12
clock advance 5s
holds shop
release H002
holds shop
balance shop
check
""",
"s3_limits": """# daily and velocity limits
open dave daily=100 velocity=3
deposit dave 500
withdraw dave 40
withdraw dave 40
withdraw dave 30
clock advance 10m
withdraw dave 10
withdraw dave 10
withdraw dave 10
balance dave
clock set 1d
withdraw dave 10
withdraw dave 10
balance dave
clock advance 20m
withdraw dave 10
balance dave
""",
"s4_settlement": """# settlement batches and a failed submission
open erin
open fred
deposit erin 10
deposit fred 20
transfer fred erin 5
settle
settle
deposit erin 1
clearing fail 1
settle
batches
clock advance 10s
clock advance 20s
batches
clearing
journal
check
""",
"s5_keys_and_reversal": """# idempotency keys and reversals
open gina
open hank
deposit gina 50 key=dep-1
deposit gina 50 key=dep-1
transfer gina hank 10 key=t1
transfer gina hank 99 key=t1
withdraw hank 3 key=t1
idem
reverse T0.1
reverse T0.1
show T0.1
show T0.3
history hank last=2
balance gina
balance hank
check
""",
}

# ====================================================================== ref_tests (ordinary behaviour)

REF_TESTS = {
"t01_basic_money": """open alice
open bob
open zed overdraft=5.5
deposit alice 1000
deposit bob 0.01
transfer alice bob 999.99
transfer bob alice 1000
withdraw zed 5.50
withdraw zed 0.01
deposit zed 5.5
accounts
balance zed
journal
check
""",
"t02_errors": """frobnicate
open
open Alice
open toolongaccountname_x
open al overdraft=-1
open al velocity=0
open al velocity=1001
open al daily=abc
open al
open al
deposit al
deposit al 0
deposit al 1.234
deposit al 12 key=bad!key
deposit al 12 key=a key=b
deposit nobody 3
deposit al 3 extra=1
withdraw al 3 tail
transfer al al 1
reverse T9.0
reverse X1
show T0.0
show T0.4096
hold al 1 ttl=500ms
hold al 1 ttl=2d
capture H1000
capture H000
release H001
clock set -5
clock advance 1x
clock set 10s
clock set 5s
clock sideways 3
history al last=0
batches last=0
clearing fail
clearing pass 3
check
""",
"t03_overdraft_and_funds": """open ann overdraft=10
open ben
deposit ann 5
withdraw ann 15
withdraw ann 0.01
deposit ben 20
transfer ben ann 20
reverse T0.4
reverse T0.0
balance ann
withdraw ann 0.01
hold ben 1
deposit ben 1
hold ben 1
balance ben
check
""",
"t04_daily_rollover": """open cat daily=100
deposit cat 1000
withdraw cat 60
withdraw cat 41
withdraw cat 40
balance cat
clock set 86399999
withdraw cat 1
balance cat
clock advance 1
balance cat
withdraw cat 100
withdraw cat 0.01
open dog daily=0
deposit dog 5
withdraw dog 0.01
transfer dog cat 1
balance dog
check
""",
"t05_velocity_rolling": """open eve velocity=2 daily=10000
deposit eve 100
clock set 30s
withdraw eve 1
clock set 90s
withdraw eve 1
withdraw eve 1
balance eve
clock set 59m
withdraw eve 1
clock set 60m30s
withdraw eve 1
balance eve
clock set 61m
withdraw eve 1
withdraw eve 1
balance eve
clock set 3h
balance eve
transfer eve eve 1
""",
"t06_reversal_rules": """open fay velocity=2 daily=30
open gus
deposit fay 100
transfer fay gus 20
withdraw fay 5
reverse T0.1
reverse T0.1
reverse T0.3
reverse T0.2
withdraw fay 5
withdraw fay 4
balance fay
balance gus
withdraw gus 20
deposit gus 3
reverse T0.0
withdraw gus 3
close gus
reverse T0.7
open gus
reverse T0.7
show T0.1
show T0.3
history fay
check
""",
"t07_holds_capture_release": """open hal
open ivy
deposit hal 100
hold hal 60 ttl=1h
hold hal 41
hold hal 40
holds hal
capture H001 amount=60.01
capture H001 amount=25 to=ivy
capture H001
capture H001 to=hal
capture H002 to=hal
capture H002 to=nobody
release H002
release H002
holds hal
balance hal
balance ivy
show T0.1
history hal
check
""",
"t08_hold_expiry_order": """open joe
deposit joe 100
clock set 1s
hold joe 1 ttl=10s
hold joe 2 ttl=5s
clock set 6s
hold joe 3 ttl=5s
hold joe 4 ttl=7s
hold joe 5 ttl=13s
hold joe 6
clock advance 2s
clock advance 3s
holds joe
clock advance 2999ms
clock advance 1ms
clock advance 1d
holds joe
balance joe
check
""",
"t09_idem_basic": """open kim daily=20
deposit kim 50 key=a1
deposit kim 70 key=a1
withdraw kim 30 key=w1
withdraw kim 15 key=w1
withdraw kim 15 key=w1
withdraw kim 15 key=w2
withdraw kim 5 key=w2
withdraw kim 50 key=a1
balance kim
idem
check
""",
"t10_idem_two_accounts": """open lea
open max
deposit lea 10 key=same
deposit max 10 key=same
deposit lea 10 key=same
transfer lea max 1 key=tx
transfer max lea 1 key=tx
transfer lea max 1 key=tx
withdraw max 1 key=tx
balance lea
balance max
idem
""",
"t11_idem_reopen_name": """open ned
deposit ned 5 key=k1
withdraw ned 5 key=k2
close ned
open ned
deposit ned 5 key=k1
withdraw ned 5 key=k2
deposit ned 5 key=k1
balance ned
show T0.2
idem
check
""",
"t26_capture_not_debit": """open opa daily=10 velocity=1
open pip
deposit opa 100
hold opa 50
hold opa 30
capture H001 amount=40 to=pip
capture H002
withdraw opa 10
withdraw opa 1
balance opa
reverse T0.1
balance opa
withdraw opa 1
check
""",
"t22_history_and_show": """open qua
open rex
deposit qua 30
transfer qua rex 1
transfer rex qua 2
hold qua 5
capture H001 to=rex
reverse T0.3
withdraw rex 1
history qua last=3
history rex last=100
history qua last=1000
show T0.3
show T0.4
show T0.6
show T0.7
open sam
history sam
check
""",
"t23_close_rules": """open tia
deposit tia 5
close tia
hold tia 5
withdraw tia 5
close tia
release H001
withdraw tia 5
close tia
close tia
balance tia
open tia overdraft=3
withdraw tia 3
close tia
deposit tia 3
close tia
accounts
check
""",
}


def t12_idem_eviction():
    out = ["open uma velocity=1000 daily=100000", "open vic velocity=1000 daily=100000",
           "open wes"]
    for i in range(40):
        out.append("deposit uma 1 key=u%02d" % i)
    out.append("deposit wes 1 key=w0")
    out.append("withdraw wes 1 key=w1")
    out.append("close wes")
    for i in range(23):
        out.append("deposit vic 1 key=v%02d" % i)
    out.append("idem")
    out.append("deposit vic 1 key=v23")
    out.append("idem")
    out.append("deposit uma 1 key=u00")
    out.append("deposit uma 1 key=u01")
    out.append("deposit uma 1 key=u39")
    out.append("deposit vic 1 key=v23")
    out.append("idem")
    out += ["balance uma", "balance vic", "check"]
    return "\n".join(out) + "\n"


def t13_slots_reuse():
    out = []
    for i in range(256):
        out.append("open s%03d" % i)
    out.append("open extra")
    out += ["close s010", "close s003", "close s200"]
    out.append("open n1")
    out.append("open n2")
    out.append("close n1")
    out.append("open n3")
    out.append("open n4")
    out.append("open n5")
    out.append("close s000")
    out.append("open n5")
    out.append("close n5")
    out.append("open n6")
    out.append("deposit n6 3")
    out.append("accounts")
    out.append("check")
    return "\n".join(out) + "\n"


def t14_hold_id_wrap():
    d = Driver()
    d("open xia")
    d("deposit xia 5000")
    for i in range(1, 1000):
        d("hold xia 1 ttl=1h")
        if i not in (7, 500, 998):
            d("release H%03d" % i)
    d("holds xia")
    d("hold xia 2 ttl=2h")
    d("hold xia 3 ttl=2h")
    d("holds xia")
    d("clock advance 1h")
    d("hold xia 4 ttl=1s")
    d("holds xia")
    d("balance xia")
    return d.text()


T15 = """open yan
open zoe
deposit yan 1
settle
settle
"""


def t15_settlement_basic():
    out = lines(T15)
    for i in range(230):
        out.append("deposit zoe %d.%02d" % (1 + i % 7, i % 100))
    out += ["settle", "settle", "settle", "settle", "batches", "batches last=2", "journal",
            "clearing", "check"]
    return "\n".join(out) + "\n"


def t16_backlog_full():
    out = ["open ada", "deposit ada 100", "clearing fail 40"]
    for i in range(16):
        out.append("deposit ada 1")
        out.append("settle")
        out.append("clock advance %ds" % (1 + i % 3))
    out.append("deposit ada 1")
    out.append("settle")
    out.append("batches last=20")
    out.append("clock advance 25s")
    out.append("clock advance 30s")
    out.append("clearing fail 0")
    out.append("clock advance 5m")
    out.append("settle")
    out.append("batches last=20")
    out.append("check")
    return "\n".join(out) + "\n"


def t17_parked():
    out = ["open bea", "deposit bea 10", "clearing fail 4", "settle"]
    out += ["clock advance 30s", "clock advance 60s", "clock advance 2m", "batches",
            "deposit bea 2", "settle", "deposit bea 3", "clearing fail 1", "settle",
            "clock advance 29999ms", "clock advance 1ms", "batches", "clearing", "check"]
    return "\n".join(out) + "\n"


def t18_compaction_blocked():
    d = Driver()
    d("open cyd velocity=1000 daily=100000")
    d("open dot")
    for i in range(700):
        d("deposit cyd %d" % (1 + i % 9))
        if i % 97 == 0:
            d("journal")
    d("journal")
    d("show T0.0")
    for _ in range(3):
        d("settle")
    d("journal")
    d("deposit cyd 1")
    for _ in range(60):
        d("deposit dot 1")
    d("journal")
    for _ in range(5):
        d("settle")
    for _ in range(140):
        d("deposit dot 2")
    d("journal")
    d("show T0.0")
    d("show T0.383")
    d("show T0.384")
    d("history cyd last=3")
    d("history dot last=2")
    d("reverse T0.5")
    d("reverse T0.700")
    d("check")
    return d.text()


def mixed_stream(seed, n, settle_every, with_holds=True, with_keys=True, churn=True):
    """A long ordinary stream: accounts come and go, money moves, holds and
    keys are used, the clock moves in whole seconds, settlement runs."""
    rng = random.Random(seed)
    d = Driver()
    names = []
    serial = 0

    def new_name():
        nonlocal serial
        serial += 1
        return "m%04d" % serial

    for _ in range(12):
        nm = new_name()
        d("open %s velocity=200 daily=100000 overdraft=%d" % (nm, rng.choice((0, 0, 50))))
        names.append(nm)
        d("deposit %s %d" % (nm, rng.randint(100, 900)))
    keyno = 0
    for step in range(n):
        r = rng.random()
        live = [nm for nm in names if d.acct(nm) is not None]
        a = rng.choice(live)
        acct = d.acct(a)
        if r < 0.22:
            key = ""
            if with_keys and rng.random() < 0.3:
                keyno += 1
                key = " key=k%d" % (keyno if rng.random() < 0.8 else max(1, keyno - rng.randint(1, 20)))
            d("deposit %s %d.%02d%s" % (a, rng.randint(1, 60), rng.randint(0, 99), key))
        elif r < 0.40:
            amt = max(1, min(acct.available(), 3000) // 100 // 3)
            d("withdraw %s %d" % (a, rng.randint(1, max(1, amt))))
        elif r < 0.60:
            b = rng.choice(live)
            if b == a:
                continue
            key = ""
            if with_keys and rng.random() < 0.3:
                keyno += 1
                key = " key=k%d" % keyno
            d("transfer %s %s %d.%02d%s" % (a, b, rng.randint(1, 20), rng.randint(0, 99), key))
        elif r < 0.68 and with_holds:
            if rng.random() < 0.5 and acct.holds:
                hid = sorted(acct.holds)[0]
                op = rng.choice(("release H%03d" % hid, "capture H%03d" % hid,
                                 "capture H%03d amount=1" % hid))
                d(op)
            else:
                ttl = rng.choice(("", " ttl=%ds" % rng.randint(1, 900)))
                d("hold %s %d%s" % (a, rng.randint(1, 30), ttl))
        elif r < 0.74:
            d("clock advance %ds" % rng.randint(1, 120))
        elif r < 0.77 and churn and len(live) > 6:
            for hid in sorted(acct.holds):
                d("release H%03d" % hid)
            bal = d.acct(a).balance
            if bal > 0:
                d("withdraw %s %d.%02d" % (a, bal // 100, bal % 100))
            elif bal < 0:
                d("deposit %s %d.%02d" % (a, -bal // 100, -bal % 100))
            d("close %s" % a)
        elif r < 0.80 and churn:
            nm = new_name()
            d("open %s velocity=200 daily=100000" % nm)
            names.append(nm)
            d("deposit %s %d" % (nm, rng.randint(50, 500)))
        elif r < 0.83:
            d(rng.choice(("balance %s" % a, "history %s last=3" % a, "holds %s" % a)))
        elif r < 0.85 and d.records:
            back = rng.randint(1, min(40, d.records))
            idx = d.records - back
            d("show T%d.%d" % (idx >> 12, idx & 4095))
        elif r < 0.87 and d.records:
            idx = d.records - rng.randint(1, min(60, d.records))
            d("reverse T%d.%d" % (idx >> 12, idx & 4095))
        if step % settle_every == settle_every - 1:
            if rng.random() < 0.15:
                d("clearing fail %d" % rng.randint(1, 2))
            d("settle")
        if step % 500 == 250:
            d("journal")
            d("idem")
            d("check")
    d("accounts")
    d("journal")
    d("batches last=5")
    d("idem")
    d("check")
    return d.text()


def t25_many_accounts():
    out = []
    for i in range(200):
        out.append("open p%03d overdraft=%d" % (i, i % 3))
        out.append("deposit p%03d %d.%02d" % (i, i, i % 100))
    for i in range(0, 200, 2):
        out.append("transfer p%03d p%03d 0.%02d" % (i + 1, i, 1 + i % 50))
    out += ["accounts", "journal", "check"]
    return "\n".join(out) + "\n"


REF_TESTS["t12_idem_eviction"] = t12_idem_eviction()
REF_TESTS["t13_slots_reuse"] = t13_slots_reuse()
REF_TESTS["t14_hold_id_wrap"] = t14_hold_id_wrap()
REF_TESTS["t15_settlement_basic"] = t15_settlement_basic()
REF_TESTS["t16_backlog_full"] = t16_backlog_full()
REF_TESTS["t17_parked"] = t17_parked()
REF_TESTS["t18_compaction_blocked"] = t18_compaction_blocked()
REF_TESTS["t19_long_mixed_a"] = mixed_stream(11, 2500, 37)
REF_TESTS["t20_long_mixed_b"] = mixed_stream(23, 3000, 53, churn=False)
REF_TESTS["t21_long_mixed_nokeys"] = mixed_stream(5, 2000, 29, with_keys=False)
REF_TESTS["t24_long_mixed_noholds"] = mixed_stream(31, 2500, 61, with_holds=False)
REF_TESTS["t25_many_accounts"] = t25_many_accounts()


# ====================================================================== ref_edge (long runs)

def fill_slots(d, prefix="a", n=256):
    for i in range(n):
        d("open %s%03d" % (prefix, i))


def e01_reuse_daily_tally():
    d = Driver()
    fill_slots(d)
    d("deposit a000 400")
    d("withdraw a000 300")
    d("withdraw a000 100")
    d("close a000")
    d("open nova")
    d("balance nova")
    d("deposit nova 600")
    d("withdraw nova 300")
    d("withdraw nova 200")
    d("balance nova")
    d("check")
    return d.text()


def e02_reuse_churn_tallies():
    rng = random.Random(202)
    d = Driver()
    fill_slots(d, "c")
    queue = ["c%03d" % i for i in range(256)]
    serial = 0
    for rnd in range(220):
        old = queue.pop(0)
        amt = rng.randint(50, 450)
        d("deposit %s %d" % (old, amt))
        d("withdraw %s %d" % (old, amt))
        d("close %s" % old)
        serial += 1
        nm = "r%04d" % serial
        d("open %s daily=%d" % (nm, rng.choice((100, 300, 500))))
        d("deposit %s 1000" % nm)
        d("withdraw %s %d" % (nm, rng.randint(60, 99)))
        if rnd % 20 == 0:
            d("balance %s" % nm)
        queue.append(nm)
        if rnd % 50 == 49:
            d("clock advance 1h")
    d("check")
    return d.text()


def epoch_stream(n_records, settle_gap, keyed_tail):
    d = Driver()
    d("open big velocity=1000 daily=100000000")
    d("open sml")
    i = 0
    while d.records < n_records:
        i += 1
        d("deposit %s %d.%02d" % ("big" if i % 3 else "sml", 1 + i % 5, i % 100))
        if i % settle_gap == 0:
            d("settle")
    d("settle")
    d("journal")
    for k in range(keyed_tail):
        d("deposit sml 1 key=late%d" % k)
        d("deposit sml 1 key=late%d" % k)
    d("show T1.1")
    d("show T1.2")
    d("settle")
    d("batches last=3")
    d("check")
    return d.text()


def compaction_case(nu_target, total, chunk_first):
    """Settle so that the first unassigned record is NU_TARGET when a later
    seal triggers compaction, then keep going."""
    d = Driver()
    d("open cmp velocity=1000 daily=100000000")
    d("open aux")
    n = 0
    while d.records < nu_target:
        n += 1
        d("deposit %s %d" % ("cmp" if n % 4 else "aux", 1 + n % 7))
        if d.records % chunk_first == 0:
            d("settle")
    while d.w.settlement.next_unassigned < nu_target:
        d("settle")
    d("journal")
    while d.records < total:
        n += 1
        d("deposit %s %d" % ("cmp" if n % 4 else "aux", 1 + n % 7))
    d("journal")
    for _ in range(3):
        d("settle")
    while d.records < total + 140:
        n += 1
        d("deposit aux 1")
    d("journal")
    d("show T0.%d" % (nu_target - 1))
    d("show T0.%d" % nu_target)
    d("batches last=4")
    d("check")
    return d.text()


def e07_lru_touch():
    out = ["open lru velocity=1000 daily=100000"]
    for i in range(64):
        out.append("deposit lru 1 key=k%02d" % i)
    out.append("deposit lru 1 key=k00")
    out.append("deposit lru 1 key=k64")
    out.append("deposit lru 1 key=k00")
    out.append("deposit lru 1 key=k01")
    out.append("deposit lru 1 key=k02")
    out += ["idem", "balance lru", "check"]
    return "\n".join(out) + "\n"


def e08_lru_long_mix():
    rng = random.Random(808)
    d = Driver()
    d("open p velocity=1000 daily=10000000")
    d("open q velocity=1000 daily=10000000")
    d("deposit p 100000")
    hot = []
    nxt = 0
    for step in range(2400):
        r = rng.random()
        acc = "p" if rng.random() < 0.7 else "q"
        if r < 0.45 or not hot:
            nxt += 1
            key = "n%d" % nxt
            hot.append((acc, key))
        elif r < 0.85:
            acc, key = hot[max(0, len(hot) - 1 - int(rng.expovariate(1 / 40.0)))]
        else:
            acc, key = rng.choice(hot)
        d("deposit %s 1 key=%s" % (acc, key))
        if step % 400 == 399:
            d("idem")
    d("balance p")
    d("balance q")
    d("check")
    return d.text()


def e09_slot_reuse_keys():
    d = Driver()
    fill_slots(d)
    d("deposit a000 5 key=pay1")
    d("withdraw a000 5 key=pay2")
    d("close a000")
    d("open fresh")
    d("deposit fresh 7 key=pay1")
    d("withdraw fresh 2 key=pay2")
    d("balance fresh")
    d("idem")
    d("check")
    return d.text()


def e10_churn_keys():
    rng = random.Random(1010)
    d = Driver()
    fill_slots(d, "k")
    queue = ["k%03d" % i for i in range(256)]
    serial = 0
    for rnd in range(300):
        old = queue.pop(0)
        if rnd < 40 or rnd % 3 == 0:
            d("deposit %s 2 key=invoice-%d" % (old, rnd % 5))
            d("withdraw %s 2" % old)
        d("close %s" % old)
        serial += 1
        nm = "j%04d" % serial
        d("open %s" % nm)
        d("deposit %s %d key=invoice-%d" % (nm, rng.randint(1, 9), rnd % 5))
        queue.append(nm)
    d("idem")
    d("check")
    return d.text()


def e11_hold_wrap_untimed():
    d = Driver()
    d("open hw")
    d("open hx")
    d("deposit hw 5000")
    d("deposit hx 100")
    d("hold hx 5")
    for i in range(2, 1000):
        d("hold hw 1 ttl=10m")
        d("release H%03d" % i)
    d("hold hw 2 ttl=10m")
    d("hold hw 3")
    d("holds hx")
    d("holds hw")
    d("release H001")
    d("holds hx")
    d("balance hx")
    d("check")
    return d.text()


def e12_hold_wrap_mixed():
    rng = random.Random(1212)
    d = Driver()
    d("open ha")
    d("open hb")
    d("deposit ha 100000")
    d("deposit hb 100000")
    for step in range(2600):
        acct = rng.choice(("ha", "hb"))
        a = d.acct(acct)
        r = rng.random()
        if r < 0.5 or not a.holds:
            ttl = "" if rng.random() < 0.08 else " ttl=%ds" % rng.randint(1, 300)
            d("hold %s %d%s" % (acct, rng.randint(1, 9), ttl))
        elif r < 0.9:
            timed = sorted(i for i in a.holds if d.w.holds.live[i].deadline is not None)
            if timed:
                op = "release" if r < 0.8 else "capture"
                d("%s H%03d" % (op, rng.choice(timed)))
        else:
            d("clock advance %ds" % rng.randint(1, 60))
        if step % 300 == 299:
            d("holds ha")
            d("check")
    d("holds ha")
    d("holds hb")
    d("check")
    return d.text()


def e13_velocity_hour_edge():
    return """open vel velocity=3 daily=100000
deposit vel 100
withdraw vel 1
clock set 20s
withdraw vel 1
clock set 59s
withdraw vel 1
withdraw vel 1
clock set 59m59s
balance vel
withdraw vel 1
clock set 60m
balance vel
withdraw vel 1
withdraw vel 1
withdraw vel 1
withdraw vel 1
balance vel
check
"""


def e14_velocity_long():
    rng = random.Random(1414)
    d = Driver()
    d("open va velocity=5 daily=100000000")
    d("open vb velocity=8 daily=100000000")
    d("deposit va 100000")
    d("deposit vb 100000")
    minute = 0
    for step in range(1500):
        acct = rng.choice(("va", "vb"))
        d("withdraw %s 1" % acct)
        if rng.random() < 0.12:
            minute += rng.choice((1, 2, 7, 13, 59, 60, 60, 60, 61))
            d("clock set %dm" % minute)
        if step % 100 == 0:
            d("balance va")
            d("balance vb")
    d("check")
    return d.text()


def e15_entry_reuse_attempts():
    out = ["open st velocity=1000", "deposit st 10", "clearing fail 2", "settle",
           "clock advance 30s", "clock advance 60s"]
    for i in range(15):
        out.append("deposit st 1")
        out.append("settle")
    out += ["deposit st 2", "clearing fail 1", "settle", "batches last=3",
            "clock advance 30s", "batches last=2", "check"]
    return "\n".join(out) + "\n"


def e16_settlement_long():
    rng = random.Random(1616)
    d = Driver()
    d("open sa velocity=1000 daily=100000000")
    d("open sb")
    for step in range(900):
        d("deposit %s %d" % (rng.choice(("sa", "sb")), rng.randint(1, 50)))
        if step % 7 == 6:
            if rng.random() < 0.3:
                d("clearing fail %d" % rng.randint(1, 3))
            d("settle")
        if step % 5 == 4:
            d("clock advance %ds" % rng.choice((10, 30, 45, 90, 240)))
    d("batches last=40")
    d("clearing")
    d("check")
    return d.text()


def e17_segment_boundaries():
    d = Driver()
    d("open sg velocity=1000 daily=100000000")
    for i in range(128):
        d("deposit sg 1")
    d("journal")
    d("show T0.127")
    d("show T0.128")
    for i in range(10):
        d("deposit sg 1")
    while d.w.settlement.next_unassigned < d.records:
        d("settle")
    while d.records < 512:
        d("deposit sg 1")
        if d.records % 100 == 0:
            d("settle")
    while d.w.settlement.next_unassigned < 500:
        d("settle")
    d("journal")
    d("show T0.383")
    d("check")
    return d.text()


def e18_segment_stats_long():
    rng = random.Random(1818)
    d = Driver()
    d("open sx velocity=1000 daily=100000000")
    d("open sy")
    for step in range(1600):
        d("deposit %s 1" % rng.choice(("sx", "sy")))
        if step % 90 == 89:
            d("settle")
        if step % 64 == 63:
            d("journal")
    d("check")
    return d.text()


def e19_hold_long_ttl():
    return """open lt
deposit lt 100
hold lt 10 ttl=30m
hold lt 20 ttl=20m
hold lt 5 ttl=2m
clock advance 13m
holds lt
balance lt
clock set 20m
holds lt
clock set 30m
holds lt
check
"""


def e20_holds_long_mixed_ttl():
    rng = random.Random(2020)
    d = Driver()
    d("open tw")
    d("deposit tw 100000")
    for step in range(1200):
        r = rng.random()
        if r < 0.45:
            ttl = rng.choice(("%ds" % rng.randint(1, 60), "%dm" % rng.randint(1, 50),
                              "%dms" % rng.randint(1000, 5000)))
            d("hold tw %d ttl=%s" % (rng.randint(1, 5), ttl))
        elif r < 0.9:
            d("clock advance %dms" % rng.randint(1, 90000))
        else:
            d("holds tw")
    d("holds tw")
    d("check")
    return d.text()


REF_EDGE = {
    "e01_reuse_daily_tally": e01_reuse_daily_tally(),
    "e02_reuse_churn_tallies": e02_reuse_churn_tallies(),
    "e03_epoch_rollover": epoch_stream(4200, 100, 3),
    "e04_epoch_keys_batches": epoch_stream(4500, 60, 20),
    "e05_compaction_partial_segment": compaction_case(127, 520, 100),
    "e06_compaction_partial_later": compaction_case(383, 900, 50),
    "e07_lru_touch": e07_lru_touch(),
    "e08_lru_long_mix": e08_lru_long_mix(),
    "e09_slot_reuse_keys": e09_slot_reuse_keys(),
    "e10_churn_keys": e10_churn_keys(),
    "e11_hold_wrap_untimed": e11_hold_wrap_untimed(),
    "e12_hold_wrap_mixed": e12_hold_wrap_mixed(),
    "e13_velocity_hour_edge": e13_velocity_hour_edge(),
    "e14_velocity_long": e14_velocity_long(),
    "e15_entry_reuse_attempts": e15_entry_reuse_attempts(),
    "e16_settlement_long": e16_settlement_long(),
    "e17_segment_boundaries": e17_segment_boundaries(),
    "e18_segment_stats_long": e18_segment_stats_long(),
    "e19_hold_long_ttl": e19_hold_long_ttl(),
    "e20_holds_long_mixed_ttl": e20_holds_long_mixed_ttl(),
}


def write(directory, cases):
    os.makedirs(directory, exist_ok=True)
    for f in os.listdir(directory):
        if f.endswith(".in") or f.endswith(".out"):
            os.remove(os.path.join(directory, f))
    for name, text in cases.items():
        with open(os.path.join(directory, name + ".in"), "w") as fh:
            fh.write(text)


def main():
    write(os.path.join(TASK, "public", "smoke"), SMOKE)
    write(os.path.join(HERE, "ref_tests"), REF_TESTS)
    write(os.path.join(HERE, "ref_edge"), REF_EDGE)
    print("inputs: smoke=%d ref_tests=%d ref_edge=%d" % (len(SMOKE), len(REF_TESTS), len(REF_EDGE)))


if __name__ == "__main__":
    main()
