#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Writes every .in file: public/smoke, private/ref_tests and private/ref_edge.

Deterministic (fixed seeds, no clock).  The matching .out files are produced
by build_private.sh from the gold tree.  Stdlib only."""
import os
import random
import shutil
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)

SETUP = """site add AMS "Amsterdam hub"
site add LHR "London Heathrow"
site add JFK "New York"
site add SFO "San Francisco"
route add R3 AMS LHR JFK
route add R4 AMS LHR JFK SFO
"""


def rd(sid, items, hum=False):
    """read lines; items are (seconds, temp[, humidity])."""
    out = []
    for it in items:
        line = "read %s t=%s temp=%s" % (sid, it[0], it[1])
        if len(it) > 2:
            line += " hum=%s" % it[2]
        out.append(line)
    return "\n".join(out) + "\n"


def flags(sid, start, step, pattern, good="5.0", bad="9.0"):
    """One reading per character of pattern: '1' in band, '0' out of band."""
    items = [(start + step * i, good if ch == "1" else bad) for i, ch in enumerate(pattern)]
    return rd(sid, items)


SMOKE = {}
TESTS = {}
EDGE = {}

# ------------------------------------------------------------------ smoke
SMOKE["s1_setup_and_read"] = SETUP + """ship add S1 "Vaccine box" route=R3 class=chilled
ship add S2 "Frozen plasma" route=R4 class=frozen hmax=70
ship show S1
ship show S2
ship list
""" + rd("S1", [(0, "4.0", 40), (60, "4.5", 42), (120, "5.0", 45), (180, "5.5", 47), (240, "6.0", 50)]) + \
    rd("S2", [(0, "-20.0"), (300, "-19.5"), (600, "-18.0")]) + """window S1
window S1 from=60 to=180
timeline S2
rollup S1
describe S1
stats
"""

SMOKE["s2_excursions_sla"] = SETUP + """set gap 400
ship add S1 "Insulin" route=R3 class=chilled
ship add S2 "Serum" route=R3 min=2.0 max=8.0
""" + rd("S1", [(0, "4.0", 40), (60, "4.5", 41), (120, "9.0", 60), (180, "9.5", 63),
                (240, "5.0", 50), (300, "5.0", 52), (900, "4.0", 49)]) + \
    rd("S2", [(0, "3.0"), (60, "3.5"), (120, "4.0"), (180, "4.5")]) + """arrive S1 stop=1 t=0
arrive S1 stop=2 t=100
arrive S1 stop=3 t=950
arrive S2 stop=1 t=10
excursions S1
alerts
sla S1
sla S2
report S1
fleet
board
"""

SMOKE["s3_export_import"] = SETUP + """ship add S1 "Cold box 7" route=R3 class=cool maxexc=20 cap=100
""" + rd("S1", [(0, "10.0", 50), (60, "11.0", 51), (120, "12.5")]) + """arrive S1 stop=1 t=0
plan S1 stop=2 t=900
export S1
import
begin export
ship	S9	Imported box	R4	1.0	6.0	-	-	-	0	0.0
r	0	30	40
r	60000	35	-
r	120000	70	42
arr	1	0
end export
ship show S9
window S9
excursions S9
export S9
"""

SMOKE["s4_find_rank"] = SETUP + """ship add S1 "Insulin pens" route=R3 class=chilled
ship add S2 "Blood samples" route=R3 class=chilled
ship add S3 "Frozen insulin" route=R4 class=frozen
ship add S4 "Spare box" route=R3
""" + flags("S1", 0, 60, "1101") + flags("S2", 0, 60, "11111") + \
    rd("S3", [(0, "-20.0"), (60, "-10.0"), (120, "-20.0")]) + """find insulin
find BLOOD
find nothing here
rank
rank by=alerts
compare S1 S2
"""

SMOKE["s5_custody_errors"] = SETUP + """ship add S1 "Orchids" route=R3 min=10.0 max=20.0
handoff S1 "Dock crew" t=100
handoff S1 "Truck 12" t=400
custody S1
verify S1 1 sig=0
read S1 t=0 temp=12.0
read S1 t=60 temp=14.0
read S1 t=120 temp=16.5
forecast S1 minutes=10
ship show S9
read S1 t=abc temp=5
arrive S1 stop=7 t=10
ship add S1 "Again" route=R3
frobnicate
help
"""

# ------------------------------------------------------------------ ref_tests
TESTS["t01_setup_show"] = """site add lhr "  London   Heathrow  "
site add AMS "Amsterdam hub"
site add ams "again"
site add X "x"
site list
route add R1 AMS LHR
route add R1 AMS LHR
route add R2 AMS
route add R3 AMS ZZZ
ship add S1 "Box one" route=R1
ship add S2 "Box two" route=R1 min=1.0 max=7.5 maxexc=30 cap=0 hmax=60 skew=-20 offset=-0.5
ship add S10 "Box ten" route=R1 class=ambient cap=5
ship add S3 "Bad band" route=R1 min=9.0 max=3.0
ship add S3 "Bad class" route=R1 class=tropical
ship add S3 "No route"
ship add S3 "Odd route" route=NOPE
ship add S1 "Dup" route=R1
ship show S1
ship show S2
ship show S10
ship list
set hold 15
set cap 0
set cap 700
set slack 0
set spike 25
set keep 90
set gap 45
set hold 0
set bogus 1
set hold 5x
config
ship show S1
ship edit S2 cap=inherit maxexc=inherit hmax=inherit skew=5
ship edit S10 class=cool
ship edit S10 min=9.5
ship edit S10 bogus=1
ship rename S1 "  Renamed   box "
ship show S2
ship show S10
ship show S1
profiles
ship remove S2
ship list
ship show S2
"""

TESTS["t02_window_ranges"] = SETUP + """ship add S1 "Range box" route=R3
read S1 t=10.5 temp=4.0 hum=40
read S1 t=11 temp=4.5
read S1 t=12 temp=5.0 hum=44
read S1 t=12.001 temp=5.5
read S1 t=20 temp=6.0
read S1 t=3600 temp=6.5
read S1 t=3600 temp=7.5
read S1 t=90061.25 temp=3.0
window S1
window S1 from=11
window S1 to=12
window S1 from=11 to=12
window S1 from=10.5 to=10.5
window S1 from=12 to=12.001
window S1 from=12.5 to=19.999
window S1 from=12 to=11
window S1 from=x
timeline S1
timeline S1 from=3600 to=100000
describe S1 from=11 to=3600
describe S1 from=100 to=200
describe S1
"""

TESTS["t03_rollup_rounding"] = SETUP + """ship add S1 "Rounding box" route=R3 min=-10.0 max=10.0
""" + rd("S1", [(0, "2.0", 45), (1, "2.1", 46), (3599.999, "-2.1"), (3600, "-2.2", 10),
                (3601, "-2.1"), (7199.999, "0.0"), (7200, "0.1", 99), (7260, "-0.1", 100),
                (10800, "9.9", 0), (10860, "-9.9")]) + """rollup S1
ship add S2 "Empty" route=R3
rollup S2
rollup S9
"""

TESTS["t04_excursions"] = SETUP + """ship add S1 "Mixed box" route=R3 min=2.0 max=8.0
""" + rd("S1", [(0, "5.0"), (60, "9.0"), (120, "9.5"), (180, "1.0"), (240, "5.0"), (300, "1.5"),
                (360, "5.0"), (420, "8.1"), (480, "8.1"), (540, "5.0"), (600, "7.0"), (660, "-3.0"),
                (720, "-3.0")]) + """excursions S1
ship add S2 "Steady" route=R3
""" + rd("S2", [(0, "5.0"), (60, "5.5")]) + """excursions S2
ship add S3 "Single" route=R3
""" + rd("S3", [(5, "30.0")]) + """excursions S3
ship add S4 "Frozen" route=R3 class=frozen
""" + rd("S4", [(0, "-20.0"), (100, "-10.0"), (200, "-12.0"), (300, "-30.0"), (400, "-20.0")]) + """excursions S4
"""

TESTS["t05_alerts_all_kinds"] = SETUP + """set hold 3
set gap 100
set spike 30
set slack 5
ship add S1 "Alert box" route=R4 hmax=65
ship add S2 "Quiet box" route=R4 maxexc=20
""" + rd("S1", [(0, "5.0", 50), (60, "5.5", 60), (120, "9.0", 70), (180, "9.0", 80),
                (240, "9.5", 66), (300, "5.0", 40), (500, "5.0"), (560, "5.4", 70), (620, "5.0", 20)]) + \
    rd("S2", [(0, "5.0"), (60, "9.0"), (120, "9.0"), (180, "9.0"), (240, "9.0"), (300, "5.0")]) + """arrive S1 stop=1 t=0
plan S1 stop=2 t=600
arrive S1 stop=2 t=1000
plan S1 stop=3 t=1000
arrive S1 stop=3 t=1000
plan S2 stop=1 t=100
arrive S2 stop=1 t=500
alerts
alerts S1
alerts S2
alerts kind=gap
alerts kind=spike
alerts S1 kind=late
alerts kind=bogus
ship edit S2 maxexc=4
alerts S2
ship edit S2 maxexc=3
alerts S2 kind=excursion
"""

TESTS["t06_cap_hours"] = SETUP + """set cap 2
ship add S1 "Cap box" route=R3
ship add S2 "Other box" route=R3 cap=1
read S1 t=3599.998 temp=5.0
read S1 t=3599.999 temp=5.1
read S1 t=3599.999 temp=5.2
read S1 t=3600 temp=5.3
read S1 t=3600.5 temp=5.4
read S1 t=3601 temp=5.5
read S1 t=3600 temp=5.6
read S2 t=10 temp=1.0
read S2 t=20 temp=2.0
read S2 t=3700 temp=3.0
stats
window S1
window S2
ship edit S2 cap=inherit
read S2 t=30 temp=4.0
read S2 t=40 temp=4.0
read S2 t=50 temp=4.0
window S2 to=100
ship edit S1 cap=3
read S1 t=7300 temp=5.0
read S1 t=7301 temp=5.0
read S1 t=7302 temp=5.0
read S1 t=7303 temp=5.0
stats
"""

TESTS["t07_sla_journeys"] = SETUP + """ship add S1 "Journey box" route=R3
ship add S2 "Open box" route=R3
ship add S3 "No readings" route=R3
""" + rd("S1", [(50, "9.0"), (200, "5.0"), (300, "9.0"), (400, "5.0"), (450, "6.0"), (600, "9.0")]) + """sla S1
arrive S1 stop=1 t=100
sla S1
arrive S1 stop=2 t=300
arrive S1 stop=3 t=500
sla S1
""" + rd("S2", [(10, "9.0"), (20, "5.0"), (30, "5.0")]) + """arrive S2 stop=1 t=15
sla S2
sla S3
arrive S3 stop=1 t=1
arrive S3 stop=1 t=2
arrive S3 stop=3 t=3
arrive S3 stop=2 t=4
arrive S3 stop=9 t=4
arrive S3 stop=0 t=4
report S3
report S2
"""

TESTS["t08_rank_orders"] = SETUP + """ship add S1 "A" route=R3
ship add S2 "B" route=R3
ship add S10 "C" route=R3
ship add S3 "D" route=R3
ship add S4 "E" route=R3
ship add S5 "No data" route=R3
""" + flags("S1", 0, 60, "10") + flags("S2", 0, 60, "01") + flags("S10", 0, 60, "1100") + \
    flags("S3", 0, 60, "111") + flags("S4", 0, 60, "1110") + """rank
rank by=alerts
rank by=exposure
rank by=speed
set slack 0
rank by=alerts
"""

TESTS["t09_prune_keep"] = SETUP + """ship add S1 "Prune box" route=R3
ship add S2 "Prune two" route=R3
""" + rd("S1", [(0, "5"), (1000, "5"), (3599.999, "5"), (3600, "5"), (3600.001, "5"), (7000, "5")]) + \
    rd("S2", [(10, "5"), (3600, "6"), (9000, "7")]) + """prune now=7200
set keep 60
prune now=3000
prune now=7200 dry=yes
prune now=7200 dry=maybe
window S1
prune now=7200
window S1
window S2
prune now=7200
set keep 0
prune now=999999
stats
set keep 1
prune now=60.5
prune now=9000.5
window S2
"""

TESTS["t10_import_roundtrip"] = SETUP + """ship add S1 "Old box" route=R3
import
begin export
ship	S1	Dock\\\\tower \\\\ crate	R4	-4.0	6.5	15	0	50	-30	0.5
r	0	-40	40
r	60000	60	-
r	120000	61	99
arr	1	0
arr	3	500000
plan	2	250000
end export
ship show S1
export S1
import
begin export
ship	S2	Second	R3	2.0	8.0	-	-	-	0	0.0
r	0	50	-
end export
export S2
export all
import
begin export
ship	S3	Broken	R3	2.0	8.0	-	-	-	0	0.0
r	0	oops	-
end export
import
begin export
ship	S3	Open block	R3	2.0	8.0	-	-	-	0	0.0
import
begin export
ship	S3	Wrong stop	R3	2.0	8.0	-	-	-	0	0.0
arr	9	500000
end export
ship list
"""

TESTS["t11_shift"] = SETUP + """ship add S1 "Shift box" route=R3
ship add S2 "Static box" route=R3
""" + rd("S1", [(100, "5.0"), (160, "6.0"), (220.5, "7.0")]) + rd("S2", [(100, "1.0")]) + """shift S1 seconds=60
window S1
shift S1 seconds=-160
window S1
shift S1 seconds=-1
window S1
shift S1 seconds=x
shift S9 seconds=1
window S2
shift S2 seconds=0
shift S2 seconds=2592000
window S2
"""

TESTS["t12_load_csv"] = SETUP + """set cap 4
ship add S1 "Csv box" route=R3 offset=0.3
load S1
t,temp,hum
0,5.0,40
60, 5.5 , 41

120,6.0,
180,6.5
240,7.0
bad row
300,x,1
360,5.0,200
end load
window S1
stats
load S9
1,1
end load
load S1
7200,5.0
7260,5.0
end load
window S1 from=7000
load S1
1,1
"""

TESTS["t13_classes"] = SETUP + """ship add S1 "Class box" route=R3 class=vaccine
ship add S2 "Class override" route=R3 class=ambient min=18.0
ship add S3 "Explicit first" route=R3 max=9.0 class=cool
ship add S4 "Order" route=R3 min=1.0 class=frozen
ship show S1
ship show S2
ship show S3
ship show S4
ship edit S1 class=frozen
ship show S1
ship edit S1 class=nonsense
ship show S1
""" + rd("S4", [(0, "-20.0"), (1, "-14.9"), (2, "-15.0"), (3, "1.0"), (4, "-25.1")]) + """excursions S4
sla S4
"""

TESTS["t14_forecast"] = SETUP + """ship add S1 "Rising" route=R3 min=2.0 max=8.0
ship add S2 "Falling" route=R3 min=-10.0 max=10.0
ship add S3 "Flat" route=R3
ship add S4 "One" route=R3
""" + rd("S1", [(0, "4.0"), (600, "4.7"), (1200, "5.4")]) + \
    rd("S2", [(0, "1.0"), (100, "0.7"), (200, "0.2"), (300, "-0.4"), (400, "-0.9"), (500, "-1.5"),
              (600, "-2.0")]) + rd("S3", [(0, "5.0"), (1000, "5.0")]) + rd("S4", [(0, "5.0")]) + """forecast S1
forecast S1 minutes=1
forecast S1 minutes=240
forecast S1 minutes=2000
forecast S2 minutes=7
forecast S2 minutes=500
forecast S3
forecast S4
forecast S9
forecast S1 minutes=0
"""

TESTS["t15_exposure_histogram"] = SETUP + """ship add S1 "Expo box" route=R3 min=2.0 max=8.0
""" + rd("S1", [(0, "5.0"), (60, "9.0"), (150, "10.5"), (210, "5.0"), (300, "1.0"), (390, "0.0"),
                (480, "5.0"), (3700, "9.0"), (3800, "9.0")]) + """exposure S1
histogram S1
histogram S1 step=25
histogram S1 step=0
ship add S2 "Neg" route=R3 min=-30.0 max=-10.0
""" + rd("S2", [(0, "-20.0"), (60, "-31.2"), (120, "-30.0"), (180, "-9.9"), (240, "-0.1"), (300, "-20.0")]) + """exposure S2
histogram S2 step=10
histogram S2 step=3
ship add S3 "Empty" route=R3
exposure S3
histogram S3
"""

TESTS["t16_custody"] = SETUP + """ship add S1 "Chain box" route=R3
handoff S1 "Zoë Müller" t=100
handoff S1 "Dock crew" t=100.5
handoff S1 "Dock crew" t=50
handoff S1 "" t=200
handoff S1 "A name that is much too long to be stored" t=300
handoff S1 "  Spaced   out  " t=86400
handoff S9 "X" t=1
custody S1
custody S9
verify S1 1 sig=0
verify S1 2 sig=0
verify S1 3 sig=0
verify S1 4 sig=0
verify S1 0 sig=0
verify S1 1 sig=100
report S1
ship remove S1
ship add S1 "Chain box" route=R3
custody S1
"""

TESTS["t17_plans_delay"] = SETUP + """set slack 0
ship add S1 "Plan box" route=R4
plan S1 stop=1 t=1000
plan S1 stop=2 t=2000
plan S1 stop=3 t=3000
plan S1 stop=4 t=4000
plan S1 stop=5 t=4000
arrive S1 stop=1 t=910
arrive S1 stop=2 t=2059
arrive S1 stop=3 t=3061
plans S1
alerts kind=late
set slack 1
alerts kind=late
set slack 2
alerts kind=late
report S1
ship add S2 "No plan" route=R3
plans S2
"""

TESTS["t18_board_fleet"] = SETUP + """ship add S1 "A very long shipment label that is cut" route=R3
ship add S2 "Ünïcödé label ünïcödé label" route=R3
ship add S3 "Short" route=R3
ship add S4 "Exactly sixteen!!" route=R3
ship add S5 "Fifteen chars!!" route=R3
board
""" + flags("S1", 0, 60, "1011") + flags("S2", 0, 60, "11") + flags("S3", 0, 60, "0") + """arrive S1 stop=1 t=0
arrive S2 stop=1 t=0
arrive S2 stop=3 t=100
fleet
board
ship remove S1
fleet
ship remove S2
ship remove S3
ship remove S4
ship remove S5
fleet
board
"""

TESTS["t19_errors"] = SETUP + """read S1 t=1 temp=1
ship add S1 "Err box" route=R3
read S1 temp=1
read S1 t=1
read S1 t=1 temp=1 hum=101
read S1 t=1 temp=1 extra=2
read S1 t=1.2345 temp=1
read S1 t=1 temp=1.25
read S1 t=1 temp=1000
read S1 t=-1 temp=1
read S1 t=1 temp=+4.5
read S1 t=2 temp=-0.5
read
read S1 S1 t=3 temp=1
arrive S1 stop=1
arrive S1 t=1
window
window S1 extra
window S1 from=1 bogus=2
rollup
excursions S1 S1
alerts S1 S1 S1
alerts S9
sla
rank now
rank extra
find
find "   "
legs
legs S9
report
export
export S9
frobnicate S1
"unterminated
ship add S2 "bad \\q escape" route=R3
ship add S3 "tab\\tinside" route=R3
ship show S3
site add AB "name" extra words
site add A1B2C3D4 "too long"
ship add S4 "x" route=R3 skew=90000
ship add S4 "x" route=R3 offset=5.1
ship add S4 "x" route=R3 offset=-5.0
ship add S4 "x" route=R3 min=2 max=
ship add S4 """ + '"' + "x" * 41 + '"' + """ route=R3
ship add S4 """ + '"' + "x" * 40 + '"' + """ route=R3
ship add S4 "x" route=R3 route=R3
stats
"""


def audit_case():
    lines = [SETUP.strip(), 'ship add S1 "Audit box" route=R3']
    for i in range(230):
        lines.append("read S1 t=%d temp=5.0" % (i * 10))
    lines += ["audit 3", "audit 0", "audit 1000", "audit x", "audit"]
    return "\n".join(lines) + "\n"


TESTS["t20_audit_wrap"] = audit_case()

TESTS["t22_hmax_zero_spike"] = SETUP + """set spike 0
ship add S1 "Humid zero" route=R3 hmax=0
ship add S2 "Humid hundred" route=R3 hmax=100
ship add S3 "No ceiling" route=R3
""" + rd("S1", [(0, "5.0", 0), (60, "5.0", 1), (120, "5.0", 0), (180, "5.0"), (240, "5.0", 50)]) + \
    rd("S2", [(0, "5.0", 100), (60, "5.0", 100)]) + rd("S3", [(0, "5.0", 100), (60, "20.0", 100)]) + """alerts kind=humid
alerts kind=spike
set spike 100
alerts kind=spike
set spike 1000
alerts kind=spike
set spike 0
set gap 0
alerts kind=gap
"""

TESTS["t23_site_export"] = """site add AAA "Plain depot"
site add BBB "Dock\\\\tower"
site add CCC "Back\\\\\\\\slash \\\\n end"
site add DDD "Zoë's café"
site export
route add R1 AAA BBB
ship add S1 "Plain label" route=R1
read S1 t=1 temp=5.0 hum=40
arr_note
export S1
export all
"""

TESTS["t24_find"] = """site add AMS "Amsterdam"
site add LHR "London"
route add R1 AMS LHR
ship add S1 "Insulin Pens" route=R1
ship add S2 "Straße samples" route=R1
ship add S3 "INSULIN (frozen)" route=R1
ship add S10 "Plain  box" route=R1
ship add S4 "Naïve crate" route=R1
find insulin
find INSULIN pens
find "insulin pens"
find strasse
find STRASSE
find "naïve"
find box
find plain box
find xyz
find (frozen)
find ""
"""

TESTS["t25_describe_compare"] = SETUP + """ship add S1 "Odd count" route=R3
ship add S2 "Even count" route=R3
ship add S3 "Empty" route=R3
""" + rd("S1", [(i * 10, t) for i, t in enumerate(["5.0", "3.1", "7.7", "4.4", "6.0", "5.5", "2.2"])]) + \
    rd("S2", [(i * 10, t) for i, t in enumerate(["5.0", "3.0", "7.1", "4.0", "6.0", "5.5", "2.2", "9.9",
                                                  "1.1", "8.8"])]) + """describe S1
describe S2
describe S3
describe S2 from=20 to=60
compare S1 S2
compare S1 S3
compare S3 S3
compare S1 S9
"""


def big_stream():
    rng = random.Random(1501)
    lines = [SETUP.strip(), "set gap 900", "set spike 40", "set slack 3"]
    ids = ["S%d" % n for n in (1, 2, 3, 10, 11, 12)]
    for k, sid in enumerate(ids):
        lines.append('ship add %s "Bulk shipment %d" route=R4 class=%s hmax=%d' % (
            sid, k, ["chilled", "vaccine", "cool", "chilled", "ambient", "chilled"][k], 55 + k * 5))
    events = []
    for sid in ids:
        t = rng.randrange(0, 600)
        temp = rng.choice([40, 50, 60, 100, 180])
        for _ in range(420):
            t += rng.choice([30, 60, 60, 90, 120, 300, 1200])
            temp += rng.randrange(-12, 13)
            temp = max(-60, min(300, temp))
            events.append((t, sid, "read %s t=%d temp=%s hum=%d" % (
                sid, t, "%d.%d" % divmod(abs(temp), 10) if temp >= 0 else "-%d.%d" % divmod(abs(temp), 10),
                rng.randrange(20, 90))))
    events.sort()
    lines.extend(e[2] for e in events)
    for n, sid in enumerate(ids):
        base = 100 + n * 50
        lines.append("arrive %s stop=1 t=%d" % (sid, base))
        lines.append("plan %s stop=2 t=%d" % (sid, base + 7000))
        lines.append("arrive %s stop=2 t=%d" % (sid, base + 7000 + (n * 97) % 600))
        lines.append("arrive %s stop=3 t=%d" % (sid, base + 20000))
    lines += ["fleet", "rank", "rank by=exposure", "rank by=alerts", "board", "alerts kind=late"]
    for sid in ids[:3]:
        lines += ["rollup " + sid, "sla " + sid, "describe " + sid, "exposure " + sid,
                  "histogram %s step=50" % sid, "excursions " + sid, "legs " + sid]
    lines += ["alerts S1", "stats"]
    return "\n".join(lines) + "\n"


TESTS["t21_big_stream"] = big_stream()

# ------------------------------------------------------------------ ref_edge
EDGE["e01_cap_zero_on_ship"] = SETUP + """set cap 2
ship add S1 "Unlimited box" route=R3 cap=0
ship add S2 "Limited box" route=R3
ship show S1
ship show S2
""" + rd("S1", [(0, "5.0"), (10, "5.1"), (20, "5.2"), (30, "5.3"), (40, "5.4")]) + \
    rd("S2", [(0, "5.0"), (10, "5.1"), (20, "5.2")]) + """window S1
window S2
stats
"""

EDGE["e02_cap_zero_global"] = SETUP + """set cap 0
config
ship add S1 "Global unlimited" route=R3
ship add S2 "Own cap" route=R3 cap=1
ship show S1
""" + rd("S1", [(i * 7, "5.0") for i in range(12)]) + rd("S2", [(0, "5.0"), (1, "5.0")]) + """stats
rollup S1
set cap 3
read S1 t=100 temp=6.0
read S1 t=101 temp=6.0
stats
ship edit S2 cap=inherit
read S2 t=5 temp=5.0
read S2 t=6 temp=5.0
read S2 t=7 temp=5.0
stats
"""

EDGE["e03_alert_hold_exact"] = SETUP + """set hold 5
ship add S1 "Hold box" route=R3 class=chilled
""" + rd("S1", [(0, "5.0"), (60, "9.0"), (120, "9.5"), (360, "5.0"), (400, "5.0"), (460, "9.0"),
                (700, "5.0"), (760, "9.0"), (1100, "9.9")]) + """excursions S1
alerts
alerts kind=excursion
report S1
"""

EDGE["e04_alert_override_open"] = SETUP + """set hold 60
ship add S1 "Short hold" route=R3 class=chilled maxexc=2
ship add S2 "Default hold" route=R3 class=chilled
""" + rd("S1", [(0, "5.0"), (10, "9.0"), (80, "9.0"), (130, "9.0")]) + \
    rd("S2", [(0, "5.0"), (10, "9.0"), (5000, "9.0")]) + """alerts
ship edit S1 maxexc=inherit
alerts S1
ship edit S1 maxexc=3
alerts S1
"""

EDGE["e05_sla_reading_at_close"] = SETUP + """ship add S1 "Close box" route=R3 class=chilled
""" + rd("S1", [(100, "5.0"), (200, "5.0"), (300, "9.0"), (500, "9.5")]) + """arrive S1 stop=1 t=100
arrive S1 stop=2 t=250
arrive S1 stop=3 t=500
sla S1
report S1
fleet
board
"""

EDGE["e06_sla_close_in_band_many"] = SETUP + """ship add S1 "Edge box" route=R3 class=chilled
ship add S2 "Second edge" route=R3 class=chilled
""" + flags("S1", 0, 100, "1101") + flags("S2", 0, 100, "000") + """arrive S1 stop=1 t=0
arrive S1 stop=3 t=300
arrive S2 stop=1 t=0
arrive S2 stop=3 t=200
sla S1
sla S2
rank
fleet
"""

EDGE["e07_legs_full_journey"] = SETUP + """ship add S1 "Leg box" route=R4 class=chilled
""" + rd("S1", [(0, "4.0"), (30, "5.0"), (100, "6.0"), (160, "7.0"), (300, "5.0"), (301, "3.0"),
                (600, "4.0")]) + """arrive S1 stop=1 t=0
arrive S1 stop=2 t=100
arrive S1 stop=3 t=300
arrive S1 stop=4 t=700
legs S1
report S1
"""

EDGE["e08_legs_partial"] = SETUP + """ship add S1 "Partial legs" route=R4 class=chilled
ship add S2 "Not started" route=R3 class=chilled
""" + rd("S1", [(10, "4.0"), (70, "4.5"), (130, "5.0")]) + """legs S1
arrive S1 stop=1 t=10
legs S1
arrive S1 stop=2 t=140
legs S1
legs S2
arrive S1 stop=4 t=1000
legs S1
"""

EDGE["e09_skew_positive"] = SETUP + """ship add S1 "Fast logger" route=R3 skew=30
""" + rd("S1", [(100, "5.0"), (160, "5.5"), (200.5, "6.0")]) + """window S1
timeline S1
ship edit S1 skew=3600
read S1 t=5000 temp=4.0
window S1 from=1000
read S1 t=3599 temp=4.0
read S1 t=3600 temp=4.0
window S1 to=100
ship show S1
"""

EDGE["e10_skew_negative"] = SETUP + """ship add S1 "Slow logger" route=R3 skew=-45
ship add S2 "Hour slow" route=R3 skew=-3600
""" + rd("S1", [(0, "5.0"), (60, "5.5")]) + rd("S2", [(0, "5.0"), (30, "5.5")]) + """window S1
window S2
rollup S2
export S1
"""

EDGE["e11_export_backslash_label"] = SETUP + """ship add S1 "C:\\\\temp\\\\new" route=R3
ship add S2 "Plain" route=R3
""" + rd("S1", [(0, "5.0"), (60, "6.0", 40)]) + """export S1
export S2
export all
"""

EDGE["e12_export_import_cycle"] = SETUP + """ship add S1 "Ends with \\\\" route=R4 class=cool maxexc=7 skew=2 offset=0.1
ship add S2 "a\\\\nb \\\\t c \\\\\\\\ d" route=R3 hmax=10
""" + rd("S1", [(0, "10.0"), (60, "9.0", 33)]) + """arrive S1 stop=1 t=0
plan S1 stop=2 t=100
export S1
export S2
ship remove S1
ship remove S2
import
begin export
ship	S1	Ends with \\\\	R4	8.0	15.0	7	-	-	2	0.1
r	0	100	-
r	60000	90	33
arr	1	0
plan	2	100000
end export
import
begin export
ship	S2	a\\\\nb \\\\t c \\\\\\\\ d	R3	2.0	8.0	-	-	10	0	0.0
end export
ship show S1
ship show S2
export S1
export S2
"""


def tie_series(sid, total, inside):
    pattern = "1" * inside + "0" * (total - inside)
    return flags(sid, 0, 60, pattern)


EDGE["e13_rank_ties_displayed"] = SETUP + "\n".join(
    'ship add %s "T%s" route=R3 class=chilled' % (sid, sid) for sid in ("S2", "S10", "S3", "S4")) + "\n" + \
    tie_series("S2", 34, 1) + tie_series("S10", 35, 1) + tie_series("S3", 35, 34) + tie_series("S4", 34, 33) + """rank
board
fleet
"""

EDGE["e14_rank_ties_many"] = SETUP + "\n".join(
    'ship add S%d "Many %d" route=R3 class=chilled' % (n, n) for n in (1, 2, 3, 9, 10, 11)) + "\n" + \
    tie_series("S1", 28, 5) + tie_series("S2", 39, 7) + tie_series("S3", 29, 3) + \
    tie_series("S9", 29, 26) + tie_series("S10", 39, 4) + tie_series("S11", 28, 23) + """rank
sla S1
sla S2
sla S3
sla S9
sla S10
sla S11
"""

EDGE["e15_find_decomposed_query"] = SETUP + """ship add S1 "Épées de Paris" route=R3
ship add S2 "Crème brûlée" route=R3
ship add S3 "Plain" route=R3
find %s
find "%s"
find %s
find "%s"
find plain
""" % (unicodedata.normalize("NFD", "épées"), unicodedata.normalize("NFD", "ÉPÉES de"),
       unicodedata.normalize("NFD", "brûlée"), unicodedata.normalize("NFD", "crème"))

EDGE["e16_find_blank_runs"] = SETUP + """ship add S1 "Cold   chain  box" route=R3
ship add S2 "Warm box" route=R3
find "cold  chain"
find "chain   box"
find "  box"
find "box  "
find cold    chain
find "COLD CHAIN BOX"
find "warm\tbox"
find "   "
"""

EDGE["e17_offset_above_range"] = SETUP + """ship add S1 "Hot logger" route=R3 offset=-0.5 min=0.0 max=50.0
ship add S2 "Cold logger" route=R3 offset=1.0 min=0.0 max=50.0
ship add S3 "Plain logger" route=R3
""" + rd("S1", [(0, "70.0"), (60, "60.4"), (120, "60.5"), (180, "61.0")]) + \
    rd("S2", [(0, "-50.0"), (60, "-41.0"), (120, "-40.5")]) + rd("S3", [(0, "99.9"), (60, "-99.9")]) + """window S1
window S2
window S3
excursions S1
export S2
"""

EDGE["e18_offset_load_path"] = SETUP + """ship add S1 "Csv hot" route=R3 offset=-5.0
ship add S2 "Csv cold" route=R3 offset=0.5
load S1
t,temp
0,70.0
60,65.5
120,50.0
end load
load S2
0,-40.5
60,-45.0
end load
window S1
window S2
histogram S1 step=100
sla S1
"""


def write_group(directory, cases):
    if os.path.isdir(directory):
        for f in os.listdir(directory):
            if f.endswith(".in") or f.endswith(".out"):
                os.remove(os.path.join(directory, f))
    os.makedirs(directory, exist_ok=True)
    for name, text in sorted(cases.items()):
        with open(os.path.join(directory, name + ".in"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)


def main():
    write_group(os.path.join(TASK, "public", "smoke"), SMOKE)
    write_group(os.path.join(HERE, "ref_tests"), TESTS)
    write_group(os.path.join(HERE, "ref_edge"), EDGE)
    print("%d smoke, %d ref_tests, %d ref_edge inputs written" % (len(SMOKE), len(TESTS), len(EDGE)))


if __name__ == "__main__":
    main()
