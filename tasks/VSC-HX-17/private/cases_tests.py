# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""ref_tests: regression inputs for documented behaviour.  Every case passes on
the original program (none of them touches a defect) and is written to fail
when one of the deliberate exceptions is "tidied up"."""
import random

T = {}


def case(name, text):
    assert name not in T, name
    T[name] = text.strip("\n") + "\n"


case("t01_setters", """
customer add c-a1 arden
set po c-a1 PO-77
set name c-a1 "Alpha One"
set tier c-a1 gold
set split c-a1 no
set hold c-a1 yes
set hold c-a1 no
set carrier c-a1 swift
set carrier c-a1 auto
set email c-a1 a@x.io
set email c-a1 -
set note c-a1 hello
set note c-a1 -
set po c-a1 -
set tier c-a1 platinum
set split c-a1 maybe
set carrier c-a1 zzz
set po c-a1 PO-77
set po c-a1 PO-77
customer show c-a1
customer history c-a1
customer add c-a1 arden
customer add bad_id arden
customer add c-a2 nowhere
customer add c-a2 crest tier=silver
customer add c-a3 gale tier=gold name="Gale Gold"
customer list
customer list tier=gold
customer list region=arden status=active
set region c-a1 crest
set region c-a1 crest
""")

case("t02_closed_accounts", """
customer add c-cl1 arden
receive harbor paper-a4 200
order add c-cl1 paper-a4:10
customer close c-cl1
set po c-cl1 X1
set name c-cl1 Renamed
set tier c-cl1 gold
set split c-cl1 no
set hold c-cl1 yes
set carrier c-cl1 swift
set region c-cl1 crest
set note c-cl1 "late note"
set note c-cl1 "later note"
audit
order add c-cl1 paper-a4:5
customer close c-cl1
customer show c-cl1
customer history c-cl1
customer list status=closed
""")

case("t03_region_guard", """
customer add c-g1 arden
customer add c-g2 gale
receive harbor paper-a4 300
receive alder cable-usb 300
order add c-g1 paper-a4:20
set region c-g1 crest
set carrier c-g1 tern
set carrier c-g2 tern
set carrier c-g2 swift
ship ORD-0001
set region c-g1 crest
set carrier c-g1 tern
customer show c-g1
set region c-g1 gale
order add c-g1 cable-usb:50
ship ORD-0002
customer show c-g1
set carrier c-g1 auto
ship ORD-0002
audit
""")

case("t04_cutoffs_iris_kelp", """
customer add c-k1 delta
receive iris paper-a4 100
receive kelp paper-a3 100
order add c-k1 paper-a4:10
order add c-k1 paper-a3:10
ship ORD-0001 at=23
tick 3
ship ORD-0002 at=0
today
order add c-k1 paper-a4:10
ship ORD-0003 at=23
tick 1
order add c-k1 paper-a3:10
ship ORD-0004 at=0
""")

case("t05_cutoff_elm_saturday", """
customer add c-e1 delta
receive elm paper-a4 400
order add c-e1 paper-a4:10
order add c-e1 paper-a4:10
order add c-e1 paper-a4:10
tick 4
ship ORD-0001 at=15
tick 1
today
ship ORD-0002 at=11
ship ORD-0003 at=13
""")

case("t06_open_days_harbor_fjord", """
customer add c-h1 gale
customer add c-h2 arden
receive harbor paper-a4 400
receive fjord paper-a3 400
order add c-h1 paper-a3:20
order add c-h2 paper-a4:20
order add c-h1 paper-a3:20
order add c-h2 paper-a4:20
ship ORD-0001
ship ORD-0002 at=20
tick 5
ship ORD-0004 at=20
tick 1
ship ORD-0003 at=10
today
""")

case("t07_cedar_capacity", """
receive cedar paper-a4 3000
stock cedar
receive cedar paper-a4 300
receive cedar paper-a4 10
receive alder paper-a4 6000
receive alder paper-a4 10
receive kelp paper-a4 400
receive kelp paper-a4 10
receive cedar paper-a4 0
receive cedar paper-a4 -5
""")

case("t08_transfer_capacity", """
receive cedar paper-a4 3300
receive harbor paper-a4 500
transfer harbor cedar paper-a4 100
transfer harbor cedar paper-a4 100
stock cedar
transfer harbor dune paper-a4 10
transfer harbor cedar paper-a4 0
transfer harbor cedar paper-a4 500
transfer cedar harbor paper-a4 200
transfer harbor harbor paper-a4 10
ledger harbor
""")

case("t09_juniper_pick_fee", """
customer add c-j1 ember
receive juniper paper-a4 100
receive juniper hammer-1 60
receive juniper bolt-m6 1000
order add c-j1 paper-a4:30 hammer-1:12 bolt-m6:200
ship ORD-0001
order add c-j1 hammer-1:6
ship ORD-0002
""")

case("t10_larch_preferred", """
customer add c-l1 gale
customer add c-l2 forge
customer add c-l3 ember
receive larch paper-a4 100
receive elm paper-a4 100
order add c-l1 paper-a4:10
order add c-l2 paper-a4:10
order add c-l3 paper-a4:10
order show ORD-0001
order show ORD-0002
order show ORD-0003
""")

case("t11_routing_split_backorder", """
customer add c-r1 crest
customer add c-r2 crest
set split c-r2 no
receive alder cable-usb 100
receive harbor cable-usb 100
receive cedar cable-usb 30
order add c-r1 cable-usb:20
order show ORD-0001
order add c-r1 cable-usb:10 cable-usb:15
order show ORD-0002
order add c-r1 cable-usb:250
order show ORD-0003
order add c-r2 cable-usb:150
order show ORD-0004
order list
order list c-r1
order list state=backorder
order list state=partial
order list c-r2 state=open
stock
""")

case("t12_pack_rounding_loose", """
receive alder bolt-m6 150
receive alder cable-usb 37
receive alder paper-a4 11
receive alder hammer-1 7
receive alder charger-20 5
receive alder tumbler-6 13
receive alder shirt-m 40
receive alder plank-2m 11
receive harbor cable-hdmi 1
stock alder
receive alder bolt-m6 0
receive alder bolt-m6 x
receive alder teleporter 5
""")

case("t13_line_rules", """
customer add c-n1 arden
receive harbor bolt-m6 3000
receive harbor tools-x 1
receive harbor hammer-1 500
receive harbor paper-a4 700
receive harbor cable-usb 2000
receive harbor tumbler-6 400
order add c-n1 bolt-m6:50
order add c-n1 bolt-m6:300
order add c-n1 bolt-m6:5000
order add c-n1 bolt-m6:5100
order add c-n1 hammer-1:1200
order add c-n1 paper-a4:600
order add c-n1 paper-a4:601
order add c-n1 cable-usb:2000
order add c-n1 cable-usb:2001
order add c-n1 tumbler-6:300
order add c-n1 tumbler-6:301
order add c-n1 bolt-m6:0
order add c-n1 bolt-m6
order add c-n1
order list
""")

case("t14_glassware_weight", """
customer add c-w1 crest
receive alder tumbler-6 120
receive alder vase-30 36
receive alder paper-a4 50
order add c-w1 tumbler-6:5
order add c-w1 vase-30:7
order add c-w1 tumbler-6:11 vase-30:3 paper-a4:5
ship ORD-0001
ship ORD-0002
ship ORD-0003
""")

case("t15_lumber_weight", """
customer add c-b1 crest
receive alder plank-2m 100
receive alder beam-3m 50
receive alder paper-a4 50
order add c-b1 plank-2m:3
order add c-b1 beam-3m:4
order add c-b1 plank-2m:5 beam-3m:10 paper-a4:3
ship ORD-0001
ship ORD-0002
ship ORD-0003
""")

case("t16_medicine_expiry", """
customer add c-m1 arden
receive dune vitamin-c 40
receive dune vitamin-c 40 exp=-3
receive dune vitamin-c 40 exp=x
receive dune vitamin-c 100 exp=45
receive dune bandage-50 40 exp=60
receive dune milk-1l 24 exp=30
receive dune pizza-fr 16 exp=30
receive alder paper-a4 20 exp=30
tick 10
order add c-m1 vitamin-c:20
order show ORD-0001
tick 5
order add c-m1 vitamin-c:20
order show ORD-0002
tick 1
order add c-m1 bandage-50:20
order add c-m1 vitamin-c:20
order show ORD-0003
order show ORD-0004
stock dune
expire
""")

case("t17_margins_boundaries", """
customer add c-q1 arden
receive dune milk-1l 120
receive dune apple-1k 100
receive dune pizza-fr 80
receive dune vitamin-c 40 exp=100
tick 6
order add c-q1 apple-1k:10
tick 1
order add c-q1 apple-1k:10
tick 11
order add c-q1 milk-1l:12
tick 1
order add c-q1 milk-1l:12
tick 51
order add c-q1 vitamin-c:20
tick 1
order add c-q1 vitamin-c:20
tick 39
order add c-q1 pizza-fr:8
tick 1
order add c-q1 pizza-fr:8
order list
stock dune
""")

case("t18_snack_margin", """
customer add c-s1 arden
receive alder crisps-50 240
receive alder bar-oat 240
tick 100
order add c-s1 crisps-50:24
tick 50
order add c-s1 crisps-50:24
order add c-s1 bar-oat:24
tick 15
order add c-s1 bar-oat:24
tick 2
order add c-s1 crisps-50:24
order show ORD-0004
order show ORD-0005
order list state=backorder
tick 14
expire
order list
stock alder
""")

case("t19_returns_windows", """
customer add c-t1 arden
receive harbor hammer-1 100
receive harbor tumbler-6 120
receive harbor milk-1l 0
receive dune milk-1l 120
receive dune apple-1k 100
receive harbor crisps-50 240
receive harbor thinner-1l 0
receive birch thinner-1l 60
receive harbor plank-2m 100
order add c-t1 hammer-1:12 tumbler-6:24
order add c-t1 milk-1l:12 apple-1k:10
order add c-t1 crisps-50:24 plank-2m:10
order add c-t1 thinner-1l:12
ship ORD-0001
ship ORD-0002
ship ORD-0003
ship ORD-0004
return ORD-0001 hammer-1 3
return ORD-0001 hammer-1 3 cond=damaged
return ORD-0001 hammer-1 9
return ORD-0002 milk-1l 2
return ORD-0002 apple-1k 2
return ORD-0003 crisps-50 4
return ORD-0003 plank-2m 4
return ORD-0004 thinner-1l 6
return ORD-0004 thinner-1l 6 cond=damaged
stock
ledger kind=return
ledger kind=scrap
""")


# ------------------------------------------------------------ carriers
class Script:
    """Small builder: numbered orders shipped one by one."""

    def __init__(self, regions, stock, tier="basic"):
        self.lines = []
        self.n = 0
        for r in regions:
            self.lines.append("customer add c-%s %s tier=%s" % (r, r, tier))
        for wh, sku, units in stock:
            self.lines.append("receive %s %s %d" % (wh, sku, units))

    def raw(self, text):
        self.lines.append(text)

    def order(self, region, items, ship=None, at=None):
        self.n += 1
        self.lines.append("order add c-%s %s" % (region, " ".join("%s:%d" % it for it in items)))
        if ship is not None:
            self.ship(self.n, ship, at)
        return self.n

    def ship(self, n, carrier=None, at=None):
        extra = ("" if carrier in (None, "") else " carrier=%s" % carrier) + ("" if at is None else " at=%d" % at)
        self.lines.append("ship ORD-%04d%s" % (n, extra))

    def text(self):
        return "\n".join(self.lines)


HARBOR_STOCK = [("harbor", "paper-a4", 600), ("harbor", "plank-2m", 200), ("harbor", "hammer-1", 120)]
PICKS = [("arden", "paper-a4", 1), ("delta", "paper-a4", 8), ("gale", "paper-a4", 20),
         ("arden", "plank-2m", 2), ("delta", "plank-2m", 7), ("gale", "plank-2m", 25),
         ("gale", "paper-a4", 3), ("arden", "plank-2m", 12), ("delta", "paper-a4", 1),
         ("gale", "hammer-1", 4), ("delta", "hammer-1", 11), ("brook", "plank-2m", 3),
         ("brook", "paper-a4", 5), ("brook", "hammer-1", 1)]


def matrix(carrier, picks=PICKS, extra=None):
    s = Script(sorted(set(r for r, _, _ in picks)), HARBOR_STOCK)
    for r, sku, qty in picks:
        s.order(r, [(sku, qty)], ship=carrier)
    for r, sku, qty, car in (extra or []):
        s.order(r, [(sku, qty)], ship=car)
    return s.text()


case("t20_carrier_swift_parcelo_haul", matrix("swift", extra=[
    ("delta", "paper-a4", 6, "parcelo"), ("delta", "paper-a4", 14, "parcelo"),
    ("gale", "hammer-1", 9, "parcelo"), ("gale", "plank-2m", 12, "parcelo"),
    ("delta", "paper-a4", 6, "haul"), ("delta", "paper-a4", 14, "haul"),
    ("gale", "plank-2m", 12, "haul"), ("gale", "plank-2m", 30, "haul"),
    ("brook", "plank-2m", 25, "parcelo")]))
case("t21_carrier_nord", matrix("nord"))
case("t22_carrier_aero", matrix("aero", extra=[("gale", "plank-2m", 12, "aero"), ("delta", "plank-2m", 9, "aero")]))
case("t23_carrier_gull", matrix("gull"))
case("t24_carrier_zed", matrix("zed", PICKS + [("delta", "paper-a4", 2), ("gale", "paper-a4", 2), ("brook", "paper-a4", 2)]))

# tern only at zone distance 0 (harbor-arden, cedar-brook, alder-crest, elm-delta, juniper-ember, dune-forge)
_s = Script(["arden", "brook", "crest", "delta", "ember", "forge", "gale", "haven", "depot"],
            [("harbor", "paper-a4", 300), ("cedar", "paper-a4", 300), ("alder", "paper-a4", 300),
             ("elm", "paper-a4", 300), ("juniper", "paper-a4", 300), ("dune", "milk-1l", 120),
             ("harbor", "hammer-1", 100), ("harbor", "plank-2m", 100)])
for r, items in (("arden", [("paper-a4", 5)]), ("arden", [("paper-a4", 30)]), ("brook", [("paper-a4", 6)]),
                 ("crest", [("paper-a4", 12)]), ("delta", [("paper-a4", 40)]), ("ember", [("paper-a4", 3)]),
                 ("forge", [("milk-1l", 12)])):
    _s.order(r, items, ship="tern")
_s.order("gale", [("paper-a4", 5)], ship="tern")
_s.order("haven", [("paper-a4", 5)], ship="tern")
_s.order("depot", [("paper-a4", 5)], ship="tern")
_s.order("arden", [("hammer-1", 10)], ship="pony")
_s.order("arden", [("hammer-1", 5)], ship="pony")
_s.order("arden", [("hammer-1", 6)], ship="pony")
_s.order("gale", [("paper-a4", 11)], ship="pony")
_s.order("gale", [("paper-a4", 10)], ship="pony")
_s.order("arden", [("plank-2m", 2)], ship="pony")
_s.order("brook", [("paper-a4", 1)], ship="pony")
case("t25_carrier_tern_pony", _s.text())

_s = Script(["arden", "brook", "crest", "delta", "ember", "forge", "gale"],
            [("harbor", "paper-a4", 400), ("harbor", "hammer-1", 200), ("harbor", "plank-2m", 200),
             ("cedar", "cable-usb", 400), ("birch", "thinner-1l", 120), ("alder", "charger-20", 100),
             ("dune", "pizza-fr", 100)])
for r in ("arden", "crest", "delta", "forge", "gale"):
    _s.order(r, [("paper-a4", 4)], ship="")
    _s.order(r, [("hammer-1", 12), ("paper-a4", 12)], ship="")
    _s.order(r, [("plank-2m", 9)], ship="")
_s.order("arden", [("thinner-1l", 6)], ship="")
_s.order("crest", [("charger-20", 8), ("cable-usb", 30)], ship="")
_s.order("ember", [("pizza-fr", 16)], ship="")
_s.order("ember", [("hammer-1", 5)], ship="swift")
_s.raw("set carrier c-ember gull")
_s.order("ember", [("hammer-1", 5)], ship="")
_s.order("ember", [("hammer-1", 5)], ship="swift")
case("t26_auto_carrier_choice", _s.text())

_s = Script(["depot", "arden"], [("harbor", "paper-a4", 100), ("alder", "paper-a4", 100)])
_s.order("depot", [("paper-a4", 10)], ship="")
_s.order("depot", [("paper-a4", 40)], ship="")
_s.order("depot", [("paper-a4", 10)], ship="haul")
_s.raw("set carrier c-depot swift")
_s.raw("set region c-depot arden")
_s.raw("set region c-arden depot")
_s.order("arden", [("paper-a4", 6)], ship="")
_s.order("depot", [("paper-a4", 6)], ship="")
_s.raw("customer show c-depot")
_s.raw("region show depot")
_s.raw("report freight_region")
case("t27_depot_pickup", _s.text())

_s = Script(["delta", "ember", "gale", "haven", "arden"],
            [("harbor", "paper-a3", 300), ("harbor", "paper-a4", 300), ("harbor", "hammer-1", 100)])
for items in ([("paper-a3", 9)], [("paper-a3", 13)], [("paper-a3", 8)], [("paper-a3", 8), ("paper-a4", 1)],
              [("hammer-1", 6)], [("paper-a4", 14)]):
    _s.order("delta", items, ship="swift")
case("t28_duty_delta", _s.text())

_s = Script(["delta", "ember", "gale", "haven", "arden"],
            [("harbor", "paper-a3", 300), ("harbor", "paper-a4", 300), ("harbor", "hammer-1", 100)])
for items in ([("paper-a3", 9)], [("paper-a3", 13)], [("paper-a3", 8)], [("paper-a3", 8), ("paper-a4", 1)],
              [("hammer-1", 6)], [("paper-a4", 14)]):
    _s.order("ember", items, ship="swift")
case("t29_duty_ember", _s.text())

_s = Script(["delta", "ember", "gale", "haven", "arden"],
            [("harbor", "paper-a3", 300), ("harbor", "paper-a4", 300), ("harbor", "hammer-1", 100)])
for r in ("gale", "haven", "arden"):
    for items in ([("paper-a3", 9)], [("paper-a4", 1)], [("paper-a3", 16)], [("hammer-1", 4)], [("paper-a3", 3)]):
        _s.order(r, items, ship="swift")
_s.raw("report duty_region")
case("t30_duty_gale_haven_arden", _s.text())

_s = Script(["forge"], [("harbor", "paper-a4", 400)])
for d in range(8):
    _s.order("forge", [("paper-a4", 5)], ship="swift")
    _s.raw("tick 1")
_s.raw("region show forge")
case("t31_forge_delivery_days", _s.text())

_s = Script(["arden"], [("harbor", "paper-a3", 300), ("harbor", "paper-a4", 300), ("harbor", "hammer-1", 200),
                        ("harbor", "plier-9", 100), ("harbor", "wrench-set", 100), ("harbor", "cable-usb", 200),
                        ("harbor", "plank-2m", 100)])
_s.raw("customer add c-gld arden tier=gold")
_s.raw("customer add c-slv arden tier=silver")
for who, items in (("gld", [("plier-9", 1), ("cable-usb", 6), ("plank-2m", 2)]),
                   ("gld", [("paper-a4", 1), ("cable-usb", 7), ("plank-2m", 3)]),
                   ("slv", [("paper-a4", 3), ("hammer-1", 4), ("plank-2m", 3)]),
                   ("slv", [("paper-a3", 1), ("plier-9", 3), ("wrench-set", 1)]),
                   ("arden", [("paper-a4", 3), ("plier-9", 7), ("plank-2m", 8)]),
                   ("arden", [("paper-a3", 1), ("plier-9", 2), ("wrench-set", 4)])):
    _s.order(who, items, ship="swift")
_s.raw("tier list")
case("t32_free_freight_tiers", _s.text())

_s = Script(["arden", "crest"], [("harbor", "paper-a4", 100), ("alder", "paper-a4", 30), ("cedar", "cable-usb", 100)])
_s.raw("customer add c-hold crest tier=gold")
_s.raw("set hold c-hold yes")
_s.raw("order add c-hold paper-a4:10")
_s.raw("set hold c-hold no")
_s.order("hold", [("paper-a4", 20)])
_s.order("hold", [("paper-a4", 500)])
_s.raw("set hold c-hold yes")
_s.order("arden", [("paper-a4", 200)])
_s.order("crest", [("paper-a4", 100)])
_s.ship(1, "swift")
_s.raw("order show ORD-0001")
_s.raw("tick 1")
_s.raw("receive harbor paper-a4 400")
_s.raw("backorder run")
_s.raw("order list state=backorder")
_s.raw("order list state=partial")
_s.raw("set hold c-hold no")
_s.raw("backorder run")
_s.raw("order list")
_s.raw("report backorders")
case("t33_holds_and_backorder_run", _s.text())

_s = Script(["arden", "crest"], [("harbor", "paper-a4", 100), ("harbor", "hammer-1", 100)])
_s.raw("customer add c-gone crest")
_s.raw("customer add c-gone2 arden")
_s.raw("customer add c-gone3 arden")
_s.order("gone", [("paper-a4", 40)])
_s.order("gone", [("paper-a4", 100)])
_s.order("gone", [("hammer-1", 6)])
_s.order("gone2", [("hammer-1", 12)])
_s.order("gone3", [("paper-a4", 20)])
_s.ship(1, "")
_s.raw("return ORD-0001 paper-a4 5")
_s.raw("customer close c-gone")
_s.raw("customer close c-gone2")
_s.raw("ship ORD-0003")
_s.raw("return ORD-0001 paper-a4 5")
_s.raw("return ORD-0003 hammer-1 1 cond=damaged")
_s.raw("order cancel ORD-0004")
_s.raw("order cancel ORD-0004")
_s.raw("receive harbor paper-a4 300")
_s.raw("backorder run")
_s.raw("order show ORD-0002")
_s.raw("ship ORD-0002")
_s.raw("order list c-gone")
_s.raw("order add c-gone paper-a4:1")
_s.raw("customer show c-gone")
case("t34_closed_account_orders", _s.text())

_s = Script([], [("harbor", "paper-a4", 100)])
for cid, tier in (("bas1", "basic"), ("sil1", "silver"), ("gol1", "gold"), ("bas2", "basic"), ("gol2", "gold"), ("sil2", "silver")):
    _s.raw("customer add c-%s arden tier=%s" % (cid, tier))
for cid in ("bas1", "sil1", "gol1", "bas2", "gol2", "sil2"):
    _s.raw("order add c-%s paper-a4:30" % cid)
_s.raw("order list")
_s.raw("tick 2")
_s.raw("receive harbor paper-a4 70")
_s.raw("backorder run")
_s.raw("order list")
_s.raw("receive harbor paper-a4 100")
_s.raw("backorder run")
_s.raw("order list state=backorder")
_s.raw("stock harbor")
case("t35_backorder_priority", _s.text())

_s = Script(["arden"], [("harbor", "paper-a4", 200), ("harbor", "hammer-1", 60), ("harbor", "cable-usb", 100)])
_s.raw("adjust harbor paper-a4 25")
_s.raw("adjust harbor paper-a4 -25")
_s.raw("adjust harbor paper-a4 -300")
_s.raw("adjust harbor paper-a4 0")
_s.raw("adjust harbor paper-a4 x")
_s.raw("adjust harbor hammer-1 5")
_s.raw("adjust nowhere hammer-1 5")
_s.raw("adjust harbor teleporter 5")
_s.raw("adjust harbor milk-1l 5")
_s.raw("adjust alder paper-a4 5")
_s.raw("receive harbor paper-a4 50")
_s.raw("adjust harbor paper-a4 -210")
_s.raw("adjust harbor paper-a4 15")
_s.raw("adjust harbor cable-usb -30")
_s.order("arden", [("hammer-1", 60)])
_s.raw("adjust harbor hammer-1 -1")
_s.raw("adjust harbor hammer-1 4")
_s.raw("stock harbor")
_s.raw("ledger harbor kind=adjust")
case("t36_adjust", _s.text())

_s = Script(["arden", "crest"], [("dune", "milk-1l", 120), ("dune", "pizza-fr", 80), ("fjord", "milk-1l", 60),
                                 ("juniper", "milk-1l", 24), ("harbor", "paper-a4", 100)])
_s.order("arden", [("milk-1l", 36), ("pizza-fr", 16)])
_s.order("crest", [("milk-1l", 12)])
_s.raw("tick 21")
_s.raw("expire fjord")
_s.raw("expire")
_s.raw("tick 1")
_s.raw("expire juniper")
_s.raw("expire fjord")
_s.raw("expire")
_s.raw("order list")
_s.raw("order show ORD-0001")
_s.raw("stock")
_s.raw("ledger kind=expire")
_s.raw("expire nowhere")
case("t37_expire_requeue", _s.text())

_s = Script(["arden"], [("alder", "paper-a4", 10), ("alder", "bolt-m6", 300), ("alder", "cable-usb", 100),
                        ("alder", "hammer-1", 12), ("alder", "charger-20", 20), ("alder", "tumbler-6", 24),
                        ("alder", "shirt-m", 60), ("alder", "crisps-50", 96), ("alder", "plank-2m", 50),
                        ("harbor", "paper-a3", 10), ("harbor", "cable-hdmi", 101), ("harbor", "bolt-m6", 500),
                        ("dune", "milk-1l", 36), ("dune", "vitamin-c", 40)])
_s.raw("replenish")
_s.raw("replenish alder")
_s.raw("report low_stock")
_s.raw("report low_stock wh=alder")
_s.order("arden", [("bolt-m6", 100), ("cable-usb", 1)])
_s.raw("replenish alder")
_s.raw("replenish nowhere")
_s.raw("receive dune vitamin-c 20 exp=300")
_s.raw("replenish dune")
case("t38_replenish_low_stock", _s.text().replace("vitamin-c 40", "vitamin-c 40 exp=200", 1))

_s = Script(["arden", "gale", "delta"], [("alder", "paper-a4", 300), ("harbor", "cable-usb", 200), ("elm", "hammer-1", 100)])
_s.raw("customer add c-gold1 gale tier=gold")
_s.order("arden", [("paper-a4", 20)])
_s.order("gale", [("cable-usb", 40)])
_s.order("delta", [("hammer-1", 10)])
_s.order("gold1", [("paper-a4", 10), ("cable-usb", 10)])
_s.order("arden", [("paper-a4", 5)])
_s.order("delta", [("cable-usb", 10)])
_s.raw("order cancel ORD-0005")
_s.raw("ship ORD-0001")
_s.raw("ship ORD-0002 carrier=gull")
_s.raw("ship ORD-0004")
_s.raw("order cancel ORD-0006")
_s.raw("order cancel ORD-0001")
_s.raw("report cancelled")
_s.raw("report status")
_s.raw("order list state=cancelled")
case("t39_cancelled_report", _s.text())

_s = Script(["arden", "gale", "delta"], [("alder", "paper-a4", 300), ("harbor", "cable-usb", 200), ("elm", "hammer-1", 100),
                                         ("dune", "milk-1l", 60), ("alder", "plank-2m", 40)])
_s.raw("customer add c-gold1 gale tier=gold")
_s.raw("customer add c-silv1 delta tier=silver")
_s.order("arden", [("paper-a4", 20)], ship="")
_s.order("gale", [("cable-usb", 40)], ship="gull")
_s.order("delta", [("hammer-1", 10)], ship="")
_s.order("gold1", [("paper-a4", 10), ("cable-usb", 10), ("plank-2m", 4)], ship="")
_s.order("silv1", [("milk-1l", 24)], ship="")
_s.order("arden", [("hammer-1", 10)])
_s.raw("tick 2")
_s.raw("return ORD-0001 paper-a4 3")
_s.raw("return ORD-0003 hammer-1 4 cond=damaged")
_s.raw("return ORD-0005 milk-1l 2")
for name in ("goods_region", "goods_customer", "goods_tier", "freight_carrier", "freight_region", "duty_region",
             "stock_cat", "stock_wh", "value_wh", "status", "backorders", "returns_cat", "scrap_cat", "expiring", "cancelled"):
    _s.raw("report %s" % name)
_s.raw("report expiring days=30")
_s.raw("report stock_wh wh=alder")
_s.raw("report goods_customer cust=c-gale")
_s.raw("report list")
_s.raw("report nosuch")
case("t40_reports_overview", _s.text())

_s = Script(["arden", "gale"], [("alder", "paper-a4", 300), ("harbor", "cable-usb", 200)])
_s.raw("customer add c-old arden")
_s.order("arden", [("paper-a4", 10)], ship="")
_s.order("gale", [("cable-usb", 10)], ship="")
_s.raw("customer close c-old")
_s.raw("report goods_customer cust=c-old")
_s.raw("report goods_region cust=c-old")
_s.raw("report goods_customer cust=c-arden")
_s.raw("report goods_customer cust=c-nobody")
_s.raw("report goods_customer cur=usd")
_s.raw("report stock_wh wh=alder")
_s.raw("report stock_wh wh=nowhere")
_s.raw("report cancelled cust=c-old")
case("t41_report_filters", _s.text())

_s = Script(["arden", "delta"], [("alder", "paper-a4", 300), ("harbor", "cable-usb", 200), ("dune", "milk-1l", 60)])
_s.order("arden", [("paper-a4", 20), ("cable-usb", 5)], ship="")
_s.order("delta", [("milk-1l", 12)], ship="")
_s.raw("order add c-delta cable-usb:3 ref=po-9")
_s.raw("return ORD-0001 paper-a4 2")
for kind in ("orders", "stock", "shipments", "ledger"):
    for fmt in ("csv", "tsv"):
        _s.raw("export %s %s" % (kind, fmt))
_s.raw("export orders json")
_s.raw("export invoices csv")
case("t42_exports", _s.text())

_s = Script(["arden", "delta"], [("alder", "paper-a4", 300), ("alder", "cable-usb", 300)])
_s.raw("order add c-arden paper-a4:10 ref=po-1")
_s.raw("order add c-arden paper-a4:10 ref=po-1")
_s.raw("order add c-delta paper-a4:10 ref=po-1")
_s.raw("order add c-arden paper-a4:5 paper-a4:7 cable-usb:3 cable-usb:4")
_s.raw("order show ORD-0003")
_s.raw("order add c-arden paper-a4:10 ref=bad/ref")
_s.raw("order add c-arden paper-a4:10 ref=po-2")
_s.raw("order cancel ORD-0001")
_s.raw("order add c-arden paper-a4:10 ref=po-1")
_s.raw("order add c-arden paper-a4:x")
_s.raw("order add c-arden paper-a4:5 bogus=1")
_s.raw("order show ORD-0099")
_s.raw("order list c-nobody")
_s.raw("order list state=weird")
case("t43_refs_duplicates_lines", _s.text())

_s = Script(["arden", "brook", "crest", "gale", "haven", "delta", "depot"],
            [("birch", "thinner-1l", 200), ("birch", "charger-20", 100), ("grove", "cleaner-5l", 100),
             ("harbor", "paper-a4", 100), ("alder", "charger-20", 100), ("fjord", "paper-a4", 100)])
for r in ("arden", "crest", "gale", "haven", "delta", "depot"):
    _s.order(r, [("thinner-1l", 6)])
    _s.order(r, [("charger-20", 4)])
    _s.order(r, [("paper-a4", 4), ("cleaner-5l", 6)])
_s.raw("region show crest")
_s.raw("region show gale")
_s.raw("region show arden")
_s.raw("region list")
_s.raw("order list")
case("t44_hazard_regions", _s.text().replace("c-brook brook", "c-brook brook"))

# a seeded random script over the safe command set (no negative adjustments, no brook customers,
# no snacks, no email changes, no goods_tier report, no forced tern)
def random_script(seed, steps):
    rnd = random.Random(seed)
    skus = ["bolt-m6", "screw-w4", "cable-usb", "cable-hdmi", "paper-a4", "paper-a3", "hammer-1", "plier-9",
            "charger-20", "tumbler-6", "vase-30", "shirt-m", "jacket-l", "milk-1l", "yogurt-4", "apple-1k",
            "pizza-fr", "peas-fr", "thinner-1l", "plank-2m", "beam-3m"]
    whs = ["alder", "birch", "cedar", "dune", "elm", "fjord", "grove", "harbor", "iris", "juniper", "kelp", "larch"]
    regs = ["arden", "crest", "delta", "ember", "forge", "gale", "haven", "depot"]
    carriers = ["swift", "parcelo", "haul", "aero", "nord", "gull", "zed", "pony", "auto", "auto", "auto"]
    custs = []
    lines = []
    for i in range(5):
        cid = "c-r%d" % i
        custs.append(cid)
        lines.append("customer add %s %s tier=%s" % (cid, rnd.choice(regs), rnd.choice(["basic", "silver", "gold"])))
    for wh in ("alder", "harbor", "cedar", "larch", "birch", "dune", "juniper", "elm"):
        for sku in rnd.sample(skus, 4):
            lines.append("receive %s %s %d" % (wh, sku, rnd.choice([20, 40, 60, 100, 240])))
    orders = 0
    for _ in range(steps):
        k = rnd.random()
        if k < 0.22:
            sel = rnd.sample(skus, rnd.choice([1, 1, 2, 3]))
            lines.append("order add %s %s" % (rnd.choice(custs),
                                              " ".join("%s:%d" % (s, rnd.choice([100, 200] if s in ("bolt-m6", "screw-w4") else [1, 2, 5, 8, 12, 20, 40])) for s in sel)))
            orders += 1
        elif k < 0.46 and orders:
            hour = rnd.choice([0, 6, 9, 10, 12, 13, 14, 16, 17, 18, 20, 23])
            extra = "" if rnd.random() < 0.6 else " carrier=%s" % rnd.choice(carriers[:-3])
            lines.append("ship ORD-%04d at=%d%s" % (rnd.randint(1, orders), hour, extra))
        elif k < 0.52:
            lines.append("tick %d" % rnd.choice([1, 1, 2, 3, 5, 9]))
        elif k < 0.60:
            lines.append("receive %s %s %d" % (rnd.choice(whs), rnd.choice(skus), rnd.choice([10, 20, 60, 120, 200])))
        elif k < 0.65 and orders:
            lines.append("order cancel ORD-%04d" % rnd.randint(1, orders))
        elif k < 0.70 and orders:
            lines.append("return ORD-%04d %s %d%s" % (rnd.randint(1, orders), rnd.choice(skus), rnd.choice([1, 2, 3, 6]),
                                                      rnd.choice(["", "", " cond=damaged"])))
        elif k < 0.75:
            lines.append("backorder run")
        elif k < 0.80:
            lines.append("transfer %s %s %s %d" % (rnd.choice(whs), rnd.choice(whs), rnd.choice(skus), rnd.choice([5, 12, 30])))
        elif k < 0.84:
            lines.append("expire %s" % rnd.choice(["", "dune", "juniper", "fjord"]))
        elif k < 0.86:
            lines.append("adjust %s %s %d" % (rnd.choice(whs), rnd.choice(skus), rnd.choice([1, 3, 12])))
        elif k < 0.90:
            lines.append("set carrier %s %s" % (rnd.choice(custs), rnd.choice(carriers)))
        elif k < 0.93:
            lines.append("set %s %s %s" % (rnd.choice(["hold", "split"]), rnd.choice(custs), rnd.choice(["yes", "no", "no"])))
        elif k < 0.95:
            lines.append("set region %s %s" % (rnd.choice(custs), rnd.choice(regs)))
        elif k < 0.97:
            lines.append("set tier %s %s" % (rnd.choice(custs), rnd.choice(["basic", "silver", "gold"])))
        else:
            lines.append("report %s" % rnd.choice(["goods_region", "goods_customer", "freight_carrier", "freight_region",
                                                   "duty_region", "stock_wh", "stock_cat", "value_wh", "status",
                                                   "backorders", "returns_cat", "scrap_cat", "low_stock"]))
    lines += ["order list", "stock", "report status", "audit 12"]
    return "\n".join(lines)


case("t45_seeded_random_a", random_script(1717, 150))
case("t46_seeded_random_b", random_script(4242, 150))

_s = Script(["arden"], [("harbor", "paper-a4", 100)])
for exp in (50, 30, 90, 30):
    _s.raw("receive dune vitamin-c 20 exp=%d" % exp)
_s.raw("receive dune vitamin-c 20 exp=100")
_s.raw("receive harbor paper-a3 50")
_s.raw("receive harbor paper-a3 50")
_s.raw("receive harbor paper-a4 30")
_s.raw("order add c-arden vitamin-c:30")
_s.raw("order show ORD-0001")
_s.raw("order add c-arden vitamin-c:40")
_s.raw("order show ORD-0002")
_s.raw("order add c-arden paper-a3:70")
_s.raw("order show ORD-0003")
_s.raw("order add c-arden paper-a4:110")
_s.raw("order show ORD-0004")
_s.raw("stock dune")
_s.raw("stock harbor sku=paper-a3")
_s.raw("stock sku=paper-a4")
_s.raw("order cancel ORD-0003")
_s.raw("order add c-arden paper-a3:10")
_s.raw("order show ORD-0005")
case("t47_fefo_pick_order", _s.text())

_s = Script(["arden"], [("harbor", "hammer-1", 100), ("harbor", "tumbler-6", 100), ("harbor", "plank-2m", 100),
                        ("dune", "apple-1k", 100), ("harbor", "charger-20", 40)])
_s.order("arden", [("hammer-1", 20), ("tumbler-6", 24), ("plank-2m", 10), ("charger-20", 8)], ship="")
_s.raw("tick 7")
_s.raw("return ORD-0001 tumbler-6 1")
_s.raw("tick 1")
_s.raw("return ORD-0001 tumbler-6 1")
_s.raw("return ORD-0001 charger-20 1")
_s.raw("tick 6")
_s.raw("return ORD-0001 charger-20 1")
_s.raw("tick 1")
_s.raw("return ORD-0001 charger-20 1")
_s.raw("return ORD-0001 plank-2m 2")
_s.raw("return ORD-0001 hammer-1 21")
_s.raw("return ORD-0001 hammer-1 19")
_s.raw("tick 15")
_s.raw("return ORD-0001 hammer-1 1")
_s.raw("return ORD-0001 plank-2m 1")
_s.raw("tick 1")
_s.raw("return ORD-0001 plank-2m 1")
_s.raw("return ORD-0001 plank-2m 1 cond=bad")
_s.raw("return ORD-0009 plank-2m 1")
_s.raw("return ORD-0001 teleporter 1")
_s.raw("return ORD-0001 paper-a4 1")
_s.raw("ledger harbor kind=return")
_s.raw("stock harbor")
case("t48_return_boundaries", _s.text())

case("t49_catalog_and_help", """
sku list
sku show bolt-m6
sku show nothing
warehouse list
warehouse show cedar
warehouse show juniper
warehouse show elm
warehouse show larch
warehouse show kelp
category list
category show cables
category show fasteners
category show medicine
category show lumber
category show glassware
category show paper
carrier list
carrier show nord
carrier show gull
carrier show zed
carrier show tern
carrier show haul
region list
region show delta
region show depot
region show haven
tier list
help
help ship
help order add
help nothing
today
tick 3
today
tick 0
tick x
tick 400000
""")

case("t50_parsing_and_errors", """
# comment line
   
customer add c-p1 arden name="Quoted Name" tier=gold
customer add c-p2 arden name="unbalanced
customer add c-p3 arden tier=gold tier=basic
customer add c-p4 arden extra=1
customer show c-p1 extra=1
set note c-p1 "two words here"
set note c-p1 plain
set note c-p1
set po c-p1 "quote ""inside"
customer show c-p1
unknowncmd
set
set color c-p1 red
order
order add
order add c-p1
order add c-p1 paper-a4:1 ref=
receive alder
receive alder paper-a4
ship
ship ORD-0001
return ORD-0001
transfer alder
adjust alder
ledger nowhere
ledger kind=weird
audit x
audit 3 action=set
audit 2 subject=c-p1
export
report
backorder
backorder walk
""")
