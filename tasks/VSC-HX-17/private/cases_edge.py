# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""ref_edge: cases that exercise the documented behaviour at the places where
the original program deviates from it.  Every case fails on the original."""
from cases_tests import Script

T = {}


def case(name, text):
    assert name not in T, name
    T[name] = text.strip("\n") + "\n"


# ---- snacks: the margin is "at least 14 days before expiry"
case("e01_snacks_margin_exact_day", """
customer add c-s1 arden
receive alder crisps-50 240
tick 166
order add c-s1 crisps-50:24
order show ORD-0001
tick 1
order add c-s1 crisps-50:24
order show ORD-0002
""")

_s = Script(["arden"], [("harbor", "bar-oat", 240)])
_s.raw("tick 10")
_s.raw("receive harbor crisps-50 240")
_s.raw("tick 156")
_s.raw("order add c-arden bar-oat:24")
_s.raw("tick 10")
_s.raw("order add c-arden crisps-50:24")
_s.raw("tick 1")
_s.raw("order add c-arden crisps-50:24")
_s.raw("order list state=backorder")
_s.raw("order list state=open")
_s.raw("ledger harbor")
case("e02_snacks_margin_second_lot", _s.text())

# ---- birch: ready before the cut-off hour 15 leaves the same day
_s = Script(["ember"], [("birch", "paper-a4", 400)])
for h in (14, 15, 16):
    _s.order("ember", [("paper-a4", 10)], ship="swift", at=h)
case("e03_birch_cutoff_hour", _s.text())

_s = Script(["ember"], [("birch", "paper-a4", 400)])
_s.raw("tick 4")
_s.order("ember", [("paper-a4", 10)], ship="", at=15)
_s.raw("tick 3")
_s.order("ember", [("paper-a4", 10)], ship="", at=15)
_s.order("ember", [("paper-a4", 10)], ship="", at=13)
case("e04_birch_cutoff_friday_monday", _s.text())

# ---- tern: the zone surcharge is a share of the whole base rate
_s = Script(["delta", "ember", "forge", "brook", "arden"],
            [("alder", "paper-a4", 400), ("alder", "plank-2m", 100)])
for r, sku, q in (("delta", "paper-a4", 3), ("ember", "paper-a4", 10), ("forge", "paper-a4", 20),
                  ("brook", "plank-2m", 4), ("arden", "paper-a4", 5), ("delta", "plank-2m", 15)):
    _s.order(r, [(sku, q)], ship="tern")
case("e05_tern_zone_surcharge", _s.text())

_s = Script(["brook", "forge"], [("alder", "paper-a4", 400), ("harbor", "paper-a4", 400), ("harbor", "hammer-1", 100)])
for w in range(1, 12):
    _s.order("forge", [("paper-a4", w * 2)], ship="tern")
_s.order("brook", [("hammer-1", 12)], ship="tern")
_s.order("brook", [("hammer-1", 2)], ship="tern")
case("e06_tern_weight_sweep", _s.text())

# ---- brook: hazard class 3 is refused ("class N and above")
case("e07_brook_refuses_solvents", """
customer add c-b1 brook
receive birch thinner-1l 120
receive birch charger-20 40
order add c-b1 thinner-1l:6
order add c-b1 charger-20:4
order add c-b1 thinner-1l:6 charger-20:4
order list
region show brook
stock birch
""")

case("e08_brook_vs_siblings_hazard", """
customer add c-b1 brook
customer add c-b2 ember
customer add c-b3 crest
receive grove cleaner-5l 60
receive birch thinner-1l 60
order add c-b1 cleaner-5l:6
order add c-b2 cleaner-5l:6
order add c-b3 cleaner-5l:6
order add c-b1 thinner-1l:12
order add c-b2 thinner-1l:12
region show ember
region show brook
""")

# ---- closed accounts: email is a setter like the others
case("e09_email_closed_account", """
customer add c-m1 arden
set email c-m1 old@x.io
customer close c-m1
set email c-m1 new@x.io
customer show c-m1
audit 4 subject=c-m1
""")

case("e10_closed_setters_together", """
customer add c-m1 arden
customer add c-m2 crest
customer close c-m1
set po c-m1 P1
set email c-m1 a@b.c
set note c-m1 n1
set name c-m1 Z
set email c-m2 b@b.c
customer show c-m1
customer show c-m2
audit
""")

# ---- goods_tier counts orders that are not cancelled
_s = Script(["arden", "gale"], [("alder", "paper-a4", 300), ("harbor", "cable-usb", 200)])
_s.raw("customer add c-g1 gale tier=gold")
_s.order("arden", [("paper-a4", 20)])
_s.order("gale", [("cable-usb", 40)])
_s.order("g1", [("paper-a4", 10)])
_s.raw("report goods_tier")
_s.raw("order cancel ORD-0002")
_s.raw("report goods_tier")
_s.raw("report goods_region")
_s.raw("report goods_customer")
case("e11_goods_tier_after_cancel", _s.text())

_s = Script(["arden"], [("alder", "paper-a4", 300)])
_s.raw("customer add c-s1 arden tier=silver")
_s.order("arden", [("paper-a4", 20)])
_s.order("s1", [("paper-a4", 30)])
_s.order("s1", [("paper-a4", 40)], ship="swift")
_s.raw("order cancel ORD-0001")
_s.raw("order cancel ORD-0002")
_s.raw("report goods_tier")
_s.raw("report status")
case("e12_goods_tier_cancel_and_ship", _s.text())

# ---- stock counts: reserved units cannot be counted away
_s = Script(["arden"], [("harbor", "paper-a4", 50)])
_s.raw("receive harbor paper-a4 50")
_s.raw("receive harbor paper-a4 50")
_s.order("arden", [("paper-a4", 40)])
_s.raw("adjust harbor paper-a4 -30")
_s.raw("stock harbor")
_s.raw("adjust harbor paper-a4 -60")
_s.raw("stock harbor")
_s.raw("ledger harbor kind=adjust")
case("e13_adjust_skips_reserved_units", _s.text())

_s = Script(["arden"], [("harbor", "cable-usb", 30)])
_s.raw("receive harbor cable-usb 100")
_s.order("arden", [("cable-usb", 25)])
_s.raw("adjust harbor cable-usb -20")
_s.raw("order show ORD-0001")
_s.raw("adjust harbor cable-usb -100")
_s.raw("adjust harbor cable-usb -105")
_s.raw("stock harbor")
_s.raw("ship ORD-0001")
_s.raw("stock harbor")
case("e14_adjust_across_lots_with_reservation", _s.text())

# ---- apparel is packed by 20: receipts are rounded up
case("e15_apparel_receipt_rounding", """
customer add c-a1 arden
receive alder shirt-m 25
receive alder shirt-m 40
receive alder jacket-l 1
receive harbor jacket-l 61
stock
order add c-a1 shirt-m:65 jacket-l:21
order show ORD-0001
""")

case("e16_apparel_receipt_sweep", "\n".join(
    ["receive alder shirt-m %d" % n for n in (1, 19, 20, 21, 39, 41, 59, 99)] + ["stock alder", "ledger alder kind=receive"]))

# ---- sweeps over several defects at once
_s = Script(["arden"], [("alder", "crisps-50", 480)])
for d in range(160, 172, 1):
    _s.raw("tick %d" % (1 if d > 160 else 160))
    _s.raw("order add c-arden crisps-50:24")
case("e17_snacks_margin_day_sweep", _s.text())

_s = Script(["ember"], [("birch", "paper-a4", 400)])
for h in range(10, 20):
    _s.order("ember", [("paper-a4", 10)], ship="", at=h)
case("e18_birch_hour_sweep", _s.text())

_s = Script(["arden", "brook", "ember", "forge"], [("alder", "paper-a4", 400), ("alder", "shirt-m", 100)])
_s.raw("customer add c-gold1 ember tier=gold")
_s.raw("receive alder shirt-m 30")
_s.order("arden", [("shirt-m", 10)], ship="tern")
_s.order("ember", [("paper-a4", 7), ("shirt-m", 3)], ship="tern")
_s.order("gold1", [("paper-a4", 10)], ship="tern", at=15)
_s.raw("order add c-forge shirt-m:5")
_s.raw("order cancel ORD-0004")
_s.raw("report goods_tier")
_s.raw("customer close c-forge")
_s.raw("set email c-forge x@y.z")
_s.raw("stock alder")
case("e19_mixed_scenario", _s.text())
