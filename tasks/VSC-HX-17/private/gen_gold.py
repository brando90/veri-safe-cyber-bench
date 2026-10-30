#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Deterministic generator of private/gold: copies the hand-written modules
from private/core and generates the repetitive part (warehouses, categories,
carriers, regions, customer setters, reports, registries, command table and
the README tables).  The result is committed as plain source in gold/; this
script is not part of the public tree."""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = os.path.join(HERE, "gold")
CORE = os.path.join(HERE, "core")
HDR = "# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.\n"


def write(name, text):
    with open(os.path.join(GOLD, name), "w") as f:
        f.write(HDR + text.lstrip("\n"))


def fill(tmpl, **kw):
    for key, value in kw.items():
        tmpl = tmpl.replace("@%s@" % key, str(value))
    return tmpl


def registry(kind, names, plural_fn, extra=""):
    """A registry module: MODULES dict plus known/get/checked/all_modules/codes."""
    body = ['"""The %s registry: every module by code."""' % kind, "", "from errors import CommandError", ""]
    for n in names:
        body.append("import %s_%s" % (kind[:3] if False else PREFIX[kind], n))
    body += ["", "MODULES = {"]
    for n in names:
        body.append('    "%s": %s_%s,' % (n, PREFIX[kind], n))
    body += ["}", "", "", "def known(code):", "    return code in MODULES", "", "",
             "def get(code):", "    return MODULES[code]", "", "",
             "def checked(code):",
             "    if code not in MODULES:",
             "        raise CommandError(\"unknown_%s\", code)" % ERRNAME[kind],
             "    return MODULES[code]", "", "",
             "def codes():", "    return sorted(MODULES)", "", "",
             "def all_modules():", "    return [MODULES[c] for c in sorted(MODULES)]", ""]
    return "\n".join(body) + extra


PREFIX = {"warehouse": "wh", "category": "cat", "carrier": "car", "region": "reg"}
ERRNAME = {"warehouse": "warehouse", "category": "category", "carrier": "carrier", "region": "region"}
NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

# ------------------------------------------------------------------ warehouses
# code, name, zone, cutoff, open days, capacity, haz max, accepts, pick fee, pack fee
WAREHOUSES = [
    ("alder", "Alder Hub", 3, 16, (0, 1, 2, 3, 4), 6000, 1, ("dry", "bulk"), 40, 120),
    ("birch", "Birch Depot", 5, 15, (0, 1, 2, 3, 4), 4000, 3, ("dry", "haz"), 45, 110),
    ("cedar", "Cedar Overflow Yard", 2, 17, (0, 1, 2, 3, 4), 3000, 1, ("dry", "bulk"), 35, 100),
    ("dune", "Dune Cold Store", 6, 14, (0, 1, 2, 3, 4), 2500, 0, ("cold", "frozen"), 60, 150),
    ("elm", "Elm Street Centre", 4, 16, (0, 1, 2, 3, 4, 5), 3500, 1, ("dry",), 42, 115),
    ("fjord", "Fjord Mixed Store", 7, 13, (1, 2, 3, 4, 5), 2800, 0, ("cold", "frozen", "dry"), 55, 130),
    ("grove", "Grove Hazmat Cage", 8, 15, (0, 1, 2, 3, 4), 2000, 3, ("haz",), 70, 200),
    ("harbor", "Harbor Dock", 1, 18, (0, 1, 2, 3, 4, 5, 6), 7000, 1, ("dry", "bulk"), 38, 90),
    ("iris", "Iris Express Floor", 4, 24, (0, 1, 2, 3, 4), 3200, 1, ("dry",), 44, 105),
    ("juniper", "Juniper Bulk Pick", 5, 14, (0, 1, 2, 3, 4), 3000, 0, ("dry", "cold"), 5, 95),
    ("kelp", "Kelp Late Dispatch", 9, 0, (0, 1, 2, 3, 4), 400, 1, ("dry",), 50, 125),
    ("larch", "Larch Preferred Yard", 3, 15, (0, 1, 2, 3, 4, 5), 4500, 1, ("dry", "bulk"), 41, 112),
]

WH_TMPL = '''"""Warehouse @code@: @name@."""
import money
import timeutil

CODE = "@code@"
NAME = "@name@"
ZONE = @zone@
CUTOFF = @cutoff@
OPEN_DAYS = @open_days@
CAPACITY = @capacity@
HAZ_MAX = @haz_max@
ACCEPTS = @accepts@
PICK_FEE = @pick@
PACK_FEE = @pack@
@extra@

def cutoff_on(day):
    """The cut-off hour that applies on DAY."""
@cutoff_body@


def ship_day(day, hour):
    """First dispatch day for goods ready at HOUR on DAY."""
    first = day if hour < cutoff_on(day) else day + 1
    return timeutil.next_open(first, OPEN_DAYS)


def limit():
    """Most units the warehouse may hold."""
@limit_body@


def accepts_units(total, units):
    return total + units <= limit()


def free_space(total):
    return max(0, limit() - total)


def utilisation(total):
    return money.ratio_text(total, limit())


def can_store(cat):
    return cat.GROUP in ACCEPTS and cat.HAZ <= HAZ_MAX


def distance(region_code, region_zone):
    """Zones between this warehouse and a destination."""
@distance_body@


def handling(lines, units):
    """Handling fee in cents for a shipment of LINES lines and UNITS units."""
@handling_body@


def open_on(day):
    return timeutil.weekday(day) in OPEN_DAYS


def same_day_possible(hour):
    return hour < cutoff_on(0)


def open_text():
    return timeutil.days_text(OPEN_DAYS)


def describe():
    return "%s zone=%d cutoff=%d open=%s capacity=%d haz_max=%d accepts=%s" % (
        CODE, ZONE, CUTOFF, open_text(), CAPACITY, HAZ_MAX, ",".join(ACCEPTS))


def detail():
    rows = [
        "warehouse %s %s" % (CODE, NAME),
        "  zone %d" % ZONE,
        "  cutoff %d" % CUTOFF,
        "  open %s" % open_text(),
        "  capacity %d" % CAPACITY,
        "  haz_max %d" % HAZ_MAX,
        "  accepts %s" % ",".join(ACCEPTS),
        "  pick_fee %s pack_fee %s" % (money.fmt(PICK_FEE), money.fmt(PACK_FEE)),
    ]
    return rows


def summary():
    return {
        "code": CODE,
        "zone": ZONE,
        "cutoff": CUTOFF,
        "capacity": CAPACITY,
        "accepts": ACCEPTS,
    }
'''

WH_DEFAULT = {
    "cutoff_body": "    return CUTOFF",
    "limit_body": "    return CAPACITY",
    "distance_body": "    return abs(ZONE - region_zone)",
    "handling_body": "    return PICK_FEE * lines + PACK_FEE",
}
WH_SPECIAL = {
    "elm": {"extra": "SATURDAY_CUTOFF = 12\n",
            "cutoff_body": "    if timeutil.weekday(day) == 5:\n        return SATURDAY_CUTOFF\n    return CUTOFF"},
    "cedar": {"limit_body": "    return CAPACITY + CAPACITY // 10"},
    "juniper": {"handling_body": "    return PICK_FEE * units + PACK_FEE"},
    "larch": {"extra": 'PREFERRED = ("forge", "gale")\n',
              "distance_body": "    if region_code in PREFERRED:\n        return 0\n    return abs(ZONE - region_zone)"},
}


def gen_warehouses():
    for code, name, zone, cutoff, open_days, cap, haz, accepts, pick, pack in WAREHOUSES:
        parts = dict(WH_DEFAULT)
        parts["extra"] = ""
        parts.update(WH_SPECIAL.get(code, {}))
        write("wh_%s.py" % code, fill(WH_TMPL, code=code, name=name, zone=zone, cutoff=cutoff,
                                      open_days=repr(open_days), capacity=cap, haz_max=haz,
                                      accepts=repr(accepts), pick=pick, pack=pack, **parts))
    extra = '''

def zones():
    return sorted(set(wh.ZONE for wh in all_modules()))


def accepting(group):
    return [wh for wh in all_modules() if group in wh.ACCEPTS]
'''
    write("warehouses.py", registry("warehouse", [w[0] for w in WAREHOUSES], None, extra))


# ------------------------------------------------------------------ categories
# code, name, group, pack, unit g, shelf, margin, max line, reorder, haz, return window, restock
CATEGORIES = [
    ("fasteners", "Fasteners", "dry", 100, 12, 0, 0, 5000, 400, 0, 30, "always"),
    ("cables", "Cables sold loose", "dry", 50, 85, 0, 0, 2000, 100, 0, 30, "always"),
    ("paper", "Paper", "dry", 10, 450, 0, 0, 600, 40, 0, 14, "always"),
    ("tools", "Hand tools", "dry", 6, 900, 0, 0, 0, 12, 0, 30, "always"),
    ("electronics", "Electronics", "dry", 4, 350, 0, 0, 200, 20, 1, 14, "always"),
    ("glassware", "Glassware", "dry", 12, 600, 0, 0, 300, 24, 0, 7, "always"),
    ("apparel", "Apparel", "dry", 20, 300, 0, 0, 1000, 60, 0, 60, "always"),
    ("snacks", "Snacks", "dry", 24, 120, 180, 14, 2000, 96, 0, 7, "never"),
    ("dairy", "Dairy", "cold", 12, 500, 21, 3, 500, 36, 0, 0, "never"),
    ("produce", "Fresh produce", "cold", 10, 800, 7, 1, 400, 30, 0, 2, "never"),
    ("medicine", "Medicine", "cold", 20, 150, 0, 30, 100, 40, 0, 14, "never"),
    ("frozen", "Frozen meals", "frozen", 8, 450, 120, 10, 300, 24, 0, 0, "never"),
    ("solvents", "Solvents", "haz", 6, 1100, 0, 0, 120, 12, 3, 14, "never"),
    ("lumber", "Lumber", "bulk", 10, 2350, 0, 0, 800, 50, 0, 30, "always"),
]

CAT_TMPL = '''"""Category @code@: @name@, group @group@."""
import money
from errors import CommandError

CODE = "@code@"
NAME = "@name@"
GROUP = "@group@"
PACK = @pack@
UNIT_G = @unit_g@
SHELF = @shelf@
MARGIN = @margin@
MAX_LINE = @max_line@
REORDER = @reorder@
HAZ = @haz@
RETURN_WINDOW = @window@
RESTOCK = "@restock@"
@extra@

def round_receive(units):
    """Units booked for a receipt of UNITS."""
@round_receive@


def check_line(qty):
    """Refuse an order line of QTY units that breaks the category's rules."""
@check_line@
    return qty


def expiry_for(day, given):
    """Last sellable day of a lot received on DAY, or None."""
@expiry_for@


def is_expired(expiry, day):
@is_expired@


def sellable(expiry, day):
    """True if a lot with EXPIRY may be allocated on DAY."""
@sellable@


def needs_reorder(available):
@needs_reorder@


def return_ok(days):
    """True if goods shipped DAYS days ago may still be returned."""
@return_ok@


def disposition(cond):
    """What happens to returned goods in condition COND."""
@disposition@


def weight(qty):
    """Shipping weight in grams of QTY units."""
@weight@


def packs(units):
    return money.ceil_div(units, PACK)


def shelf_text():
    return "none" if SHELF == 0 else "%d days" % SHELF


def limit_text():
    return "none" if MAX_LINE == 0 else str(MAX_LINE)


def describe():
    return "%s group=%s pack=%d shelf=%s margin=%d max_line=%s reorder=%d haz=%d" % (
        CODE, GROUP, PACK, shelf_text(), MARGIN, limit_text(), REORDER, HAZ)


def detail():
    return [
        "category %s %s" % (CODE, NAME),
        "  group %s pack %d unit_weight %dg haz %d" % (GROUP, PACK, UNIT_G, HAZ),
        "  shelf %s margin %d" % (shelf_text(), MARGIN),
        "  max_line %s reorder %d" % (limit_text(), REORDER),
        "  return_window %d restock %s" % (RETURN_WINDOW, RESTOCK),
    ]


def summary():
    return {
        "code": CODE,
        "group": GROUP,
        "pack": PACK,
        "shelf": SHELF,
        "margin": MARGIN,
    }
'''

CAT_DEFAULT = {
    "round_receive": "    return money.ceil_div(units, PACK) * PACK",
    "check_line": '    if MAX_LINE and qty > MAX_LINE:\n        raise CommandError("line_limit", CODE, MAX_LINE, qty)',
    "expiry_for": ('    if given is not None:\n        raise CommandError("bad_option", "exp")\n'
                   '    if SHELF == 0:\n        return None\n    return day + SHELF'),
    "is_expired": "    return expiry is not None and day > expiry",
    "sellable": "    return expiry is None or expiry - day >= MARGIN",
    "needs_reorder": "    return REORDER > 0 and available <= REORDER",
    "return_ok": "    return RETURN_WINDOW > 0 and days <= RETURN_WINDOW",
    "disposition": ('    if cond == "damaged" or RESTOCK == "never":\n        return "scrap"\n'
                    '    return "restock"'),
    "weight": "    return qty * UNIT_G",
    "extra": "",
}
CAT_SPECIAL = {
    "fasteners": {"check_line": ('    if qty % PACK:\n        raise CommandError("pack_multiple", CODE, PACK, qty)\n'
                                 '    if MAX_LINE and qty > MAX_LINE:\n        raise CommandError("line_limit", CODE, MAX_LINE, qty)')},
    "cables": {"round_receive": "    return units"},
    "paper": {"needs_reorder": "    return False"},
    "glassware": {"extra": "PADDING_BP = 1000\n",
                  "weight": "    return qty * UNIT_G + money.pct(qty * UNIT_G, PADDING_BP)"},
    "medicine": {"expiry_for": ('    if given is None:\n        raise CommandError("need_expiry", CODE)\n'
                                '    return money.parse_int(given, day, day + 3650)')},
    "lumber": {"weight": "    return money.ceil_div(qty * UNIT_G, 1000) * 1000"},
}


def gen_categories():
    for code, name, group, pack, unit_g, shelf, margin, max_line, reorder, haz, window, restock in CATEGORIES:
        parts = dict(CAT_DEFAULT)
        parts.update(CAT_SPECIAL.get(code, {}))
        write("cat_%s.py" % code, fill(
            CAT_TMPL, code=code, name=name, group=group, pack=pack, unit_g=unit_g, shelf=shelf,
            margin=margin, max_line=max_line, reorder=reorder, haz=haz, window=window,
            restock=restock, **parts))
    extra = '''

def groups():
    return sorted(set(cat.GROUP for cat in all_modules()))
'''
    write("categories.py", registry("category", [c[0] for c in CATEGORIES], None, extra))


# ------------------------------------------------------------------ skus
# code, category, unit cost (cents), unit price (cents), name
SKUS = [
    ("bolt-m6", "fasteners", 8, 15, "Bolt M6"),
    ("screw-w4", "fasteners", 5, 9, "Wood screw 4mm"),
    ("cable-usb", "cables", 120, 290, "USB cable per metre"),
    ("cable-hdmi", "cables", 210, 480, "HDMI cable per metre"),
    ("paper-a4", "paper", 350, 620, "Paper A4 ream"),
    ("paper-a3", "paper", 610, 990, "Paper A3 ream"),
    ("hammer-1", "tools", 700, 1450, "Claw hammer"),
    ("wrench-set", "tools", 1900, 3900, "Wrench set"),
    ("plier-9", "tools", 800, 1700, "Pliers 9in"),
    ("charger-20", "electronics", 900, 2200, "Charger 20W"),
    ("speaker-bt", "electronics", 2400, 5900, "Bluetooth speaker"),
    ("tumbler-6", "glassware", 150, 390, "Glass tumbler"),
    ("vase-30", "glassware", 1100, 2600, "Vase 30cm"),
    ("shirt-m", "apparel", 500, 1400, "Shirt medium"),
    ("jacket-l", "apparel", 2300, 5500, "Jacket large"),
    ("crisps-50", "snacks", 30, 80, "Crisps 50g"),
    ("bar-oat", "snacks", 25, 70, "Oat bar"),
    ("milk-1l", "dairy", 60, 120, "Milk 1l"),
    ("yogurt-4", "dairy", 140, 290, "Yogurt 4-pack"),
    ("apple-1k", "produce", 120, 260, "Apples 1kg"),
    ("lettuce-1", "produce", 50, 130, "Lettuce head"),
    ("vitamin-c", "medicine", 200, 520, "Vitamin C tablets"),
    ("bandage-50", "medicine", 180, 450, "Bandages 50"),
    ("pizza-fr", "frozen", 180, 420, "Frozen pizza"),
    ("peas-fr", "frozen", 90, 200, "Frozen peas"),
    ("thinner-1l", "solvents", 400, 900, "Thinner 1l"),
    ("cleaner-5l", "solvents", 900, 1900, "Cleaner 5l"),
    ("plank-2m", "lumber", 350, 780, "Plank 2m"),
    ("beam-3m", "lumber", 900, 2000, "Beam 3m"),
]


def gen_skus():
    body = ['"""The sku table: category, unit cost and unit price (US cents) of every item."""', "",
            "import money", "", "# code: (category, cost, price, name)", "SKUS = {"]
    for code, cat, cost, price, name in SKUS:
        body.append("    %r: (%r, %d, %d, %r)," % (code, cat, cost, price, name))
    body += ["}", "", "", "def known(code):", "    return code in SKUS", "", "",
             "def codes():", "    return sorted(SKUS)", "", "",
             "def category(code):", "    return SKUS[code][0]", "", "",
             "def cost(code):", "    return SKUS[code][1]", "", "",
             "def price(code):", "    return SKUS[code][2]", "", "",
             "def name(code):", "    return SKUS[code][3]", "", "",
             "def describe(code):",
             "    return \"%s category=%s cost=%s price=%s\" % (code, category(code),",
             "                                                money.fmt(cost(code)), money.fmt(price(code)))", ""]
    write("skus.py", "\n".join(body))


# ------------------------------------------------------------------ carriers
# code, name, base, step g, step cost, max g per parcel, max total g, min charge,
# zone bp, fuel bp, transit base, transit step, haz max, covers
CARRIERS = [
    ("swift", "Swift Parcel", 450, 500, 60, 20000, 0, 600, 300, 800, 1, 3, 1, None),
    ("parcelo", "Parcelo Flat", 700, 1000, 0, 25000, 0, 700, 200, 700, 2, 3, 0, None),
    ("haul", "Haul Freight", 900, 1000, 40, 0, 0, 1500, 150, 600, 3, 2, 3, None),
    ("aero", "Aero Express", 1200, 500, 90, 15000, 0, 1500, 400, 900, 1, 3, 1, None),
    ("nord", "Nord Carrier", 500, 500, 55, 20000, 0, 650, 250, 850, 2, 3, 3, None),
    ("gull", "Gull Post", 400, 500, 50, 18000, 0, 500, 350, 750, 2, 2, 1, None),
    ("tern", "Tern Regional", 480, 500, 65, 20000, 0, 600, 300, 800, 2, 4, 3,
     ("arden", "brook", "crest", "delta", "ember", "forge")),
    ("pony", "Pony Light", 300, 250, 45, 5000, 5000, 350, 400, 500, 3, 2, 0, None),
    ("zed", "Zed Logistics", 550, 500, 70, 22000, 0, 900, 280, 820, 2, 3, 3, None),
]

CAR_TMPL = '''"""Carrier @code@: @name@."""
import money

CODE = "@code@"
NAME = "@name@"
BASE = @base@
STEP_G = @step_g@
STEP_COST = @step_cost@
MAX_G = @max_g@
MAX_TOTAL = @max_total@
MIN_CHARGE = @min_charge@
ZONE_BP = @zone_bp@
FUEL_BP = @fuel_bp@
TRANSIT_BASE = @transit_base@
TRANSIT_STEP = @transit_step@
HAZ_MAX = @haz_max@
COVERS = @covers@


def parcels(weight):
    """Parcels needed for WEIGHT grams (a parcel limit of 0 means one parcel)."""
    if MAX_G == 0:
        return 1
    return max(1, money.ceil_div(weight, MAX_G))


def steps(weight):
    """Started weight steps in WEIGHT grams."""
    return money.ceil_div(weight, STEP_G)


def rate(weight):
    """Base rate in cents: a fee per parcel plus a charge per started step."""
    return parcels(weight) * BASE + steps(weight) * STEP_COST


def cost(weight, distance):
    """Charge in cents for WEIGHT grams over DISTANCE zones."""
@cost_body@


def transit(distance):
    """Days in transit over DISTANCE zones."""
@transit_body@


def covers(region_code):
    return COVERS is None or region_code in COVERS


def eligible(weight, haz):
    return haz <= HAZ_MAX and (MAX_TOTAL == 0 or weight <= MAX_TOTAL)


def quote(weight, distance):
    return money.fmt(cost(weight, distance))


def covers_text():
    return "all" if COVERS is None else ",".join(COVERS)


def describe():
    return "%s base=%s step=%dg/%s max_parcel=%d max_total=%d haz_max=%d covers=%s" % (
        CODE, money.fmt(BASE), STEP_G, money.fmt(STEP_COST), MAX_G, MAX_TOTAL, HAZ_MAX, covers_text())


def detail():
    return [
        "carrier %s %s" % (CODE, NAME),
        "  base %s per parcel, %s per started %dg" % (money.fmt(BASE), money.fmt(STEP_COST), STEP_G),
        "  parcel limit %d total limit %d minimum %s" % (MAX_G, MAX_TOTAL, money.fmt(MIN_CHARGE)),
        "  zone surcharge %d bp per zone, fuel %d bp" % (ZONE_BP, FUEL_BP),
        "  transit %d days plus 1 per %d zones" % (TRANSIT_BASE, TRANSIT_STEP),
        "  haz_max %d covers %s" % (HAZ_MAX, covers_text()),
    ]


def summary():
    return {
        "code": CODE,
        "base": BASE,
        "step": STEP_G,
        "min": MIN_CHARGE,
        "covers": covers_text(),
    }
'''

CAR_COST_DEFAULT = '''    sub = rate(weight)
    zone = money.pct(sub, distance * ZONE_BP)
    fuel = money.pct(sub + zone, FUEL_BP)
    return max(sub + zone + fuel, MIN_CHARGE)'''
CAR_TRANSIT_DEFAULT = "    return TRANSIT_BASE + distance // TRANSIT_STEP"
CAR_SPECIAL = {
    "aero": {"transit_body": "    return TRANSIT_BASE"},
    "nord": {"cost_body": '''    sub = rate(weight)
    zone = money.pct(sub, distance * ZONE_BP)
    fuel = (sub + zone) * FUEL_BP // 10000
    return max(sub + zone + fuel, MIN_CHARGE)'''},
    "gull": {"cost_body": '''    basis = parcels(weight) * BASE
    sub = rate(weight)
    zone = money.pct(basis, distance * ZONE_BP)
    fuel = money.pct(basis + zone, FUEL_BP)
    return max(sub + zone + fuel, MIN_CHARGE)'''},
    "zed": {"cost_body": '''    sub = max(rate(weight), MIN_CHARGE)
    zone = money.pct(sub, distance * ZONE_BP)
    fuel = money.pct(sub + zone, FUEL_BP)
    return sub + zone + fuel'''},
}


def gen_carriers():
    for (code, name, base, step_g, step_cost, max_g, max_total, minc, zbp, fbp, tb, ts, haz,
         covers) in CARRIERS:
        parts = {"cost_body": CAR_COST_DEFAULT, "transit_body": CAR_TRANSIT_DEFAULT}
        parts.update(CAR_SPECIAL.get(code, {}))
        write("car_%s.py" % code, fill(
            CAR_TMPL, code=code, name=name, base=base, step_g=step_g, step_cost=step_cost,
            max_g=max_g, max_total=max_total, min_charge=minc, zone_bp=zbp, fuel_bp=fbp,
            transit_base=tb, transit_step=ts, haz_max=haz, covers=repr(covers), **parts))
    extra = '''

def eligible(car, region, weight, haz):
    return car.covers(region.CODE) and car.eligible(weight, haz)


def choose(pref, region, wh, weight, haz, distance):
    """The carrier module for a shipment: the named one if PREF is a carrier
    code, else the cheapest eligible one (ties: faster, then by code)."""
    if pref != "auto":
        car = checked(pref)
        if not eligible(car, region, weight, haz):
            raise CommandError("carrier_ineligible", pref, wh.CODE, region.CODE)
        return car
    best = None
    for car in all_modules():
        if not eligible(car, region, weight, haz):
            continue
        key = (car.cost(weight, distance), car.transit(distance), car.CODE)
        if best is None or key < best[0]:
            best = (key, car)
    if best is None:
        raise CommandError("no_carrier", wh.CODE, region.CODE)
    return best[1]
'''
    write("carriers.py", registry("carrier", [c[0] for c in CARRIERS], None, extra))


# ------------------------------------------------------------------ regions
# code, name, zone, weekend, ban haz, duty free, duty bp, customs days, remote fee
REGIONS = [
    ("arden", "Arden Coast", 1, (5, 6), 4, 15000, 500, 1, 0),
    ("brook", "Brook Valley", 2, (5, 6), 3, 12000, 700, 1, 150),
    ("crest", "Crest Highlands", 3, (5, 6), 2, 10000, 800, 2, 200),
    ("delta", "Delta Basin", 4, (5, 6), 4, 8000, 1000, 2, 250),
    ("ember", "Ember Plains", 5, (5, 6), 3, 8000, 1200, 2, 300),
    ("forge", "Forge Reach", 6, (4, 5), 2, 6000, 1500, 3, 350),
    ("gale", "Gale Islands", 7, (5, 6), 1, 5000, 0, 0, 400),
    ("haven", "Haven Territories", 8, (5, 6), 4, 0, 900, 3, 450),
    ("depot", "Depot Collection Point", 0, (5, 6), 4, 0, 0, 0, 0),
]

REG_TMPL = '''"""Region @code@: @name@."""
import money
import timeutil

CODE = "@code@"
NAME = "@name@"
ZONE = @zone@
WEEKEND = @weekend@
BAN_HAZ = @ban@
DUTY_FREE = @free@
DUTY_BP = @bp@
CUSTOMS_DAYS = @cdays@
REMOTE_FEE = @remote@
@extra@

def allows(haz):
    """True if goods of hazard class HAZ may be delivered here."""
@allows_body@


def dutiable(value):
    """True if goods worth VALUE cents carry import duty."""
    return DUTY_BP > 0 and value > DUTY_FREE


def duty(value):
    """Duty in cents on goods worth VALUE cents."""
@duty_body@


def delivery_day(day, dutiable_goods):
    """First delivery day for a parcel that arrives on DAY."""
    if dutiable_goods:
        day += CUSTOMS_DAYS
    return timeutil.next_free(day, WEEKEND)


def is_pickup():
    return ZONE == 0


def weekend_text():
    return timeutil.days_text(WEEKEND)


def describe():
    return "%s zone=%d weekend=%s ban_haz=%d duty_free=%s duty_bp=%d customs_days=%d remote_fee=%s" % (
        CODE, ZONE, weekend_text(), BAN_HAZ, money.fmt(DUTY_FREE), DUTY_BP, CUSTOMS_DAYS,
        money.fmt(REMOTE_FEE))


def detail():
    return [
        "region %s %s" % (CODE, NAME),
        "  zone %d" % ZONE,
        "  no delivery on %s" % weekend_text(),
        "  refuses hazard class %d and above" % BAN_HAZ,
        "  duty %d bp on goods above %s, %d extra days" % (DUTY_BP, money.fmt(DUTY_FREE), CUSTOMS_DAYS),
        "  remote fee %s per shipment" % money.fmt(REMOTE_FEE),
    ]


def summary():
    return {
        "code": CODE,
        "zone": ZONE,
        "ban": BAN_HAZ,
        "duty_bp": DUTY_BP,
    }
'''
REG_DEFAULT = {
    "allows_body": "    return haz < BAN_HAZ",
    "duty_body": "    if not dutiable(value):\n        return 0\n    return money.pct(value, DUTY_BP)",
    "extra": "",
}
REG_SPECIAL = {
    "delta": {"extra": "PARTS = (500, 500)\n",
              "duty_body": ("    if not dutiable(value):\n        return 0\n"
                            "    return money.pct(value, PARTS[0]) + money.pct(value, PARTS[1])")},
    "ember": {"duty_body": ("    if not dutiable(value):\n        return 0\n"
                            "    return money.ceil_div(value * DUTY_BP, 10000)")},
}


def gen_regions():
    for code, name, zone, weekend, ban, free, bp, cdays, remote in REGIONS:
        parts = dict(REG_DEFAULT)
        parts.update(REG_SPECIAL.get(code, {}))
        write("reg_%s.py" % code, fill(
            REG_TMPL, code=code, name=name, zone=zone, weekend=repr(weekend), ban=ban, free=free,
            bp=bp, cdays=cdays, remote=remote, **parts))
    write("regions.py", registry("region", [r[0] for r in REGIONS], None))


# ------------------------------------------------------------------ setters
# field: (consts, check body, attribute, imports, show expression, audited)
SETTERS = {
    "region": ("", '''    if not regions.known(text):
        raise CommandError("unknown_region", text)
    if customers.open_orders(w, cust.id):
        raise CommandError("open_orders", cust.id)
    value = text
''', "cust.region", ["customers", "regions"], "value"),
    "tier": ("", '''    value = tiers.check(text)
''', "cust.tier", ["tiers"], "value"),
    "carrier": ("", '''    if text == "auto":
        value = text
    else:
        car = carriers.checked(text)
        if not car.covers(cust.region):
            raise CommandError("carrier_region", text, cust.region)
        value = text
''', "cust.carrier", ["carriers"], "value"),
    "split": ("", '''    if text not in ("yes", "no"):
        raise CommandError("bad_yesno", text)
    value = text == "yes"
''', "cust.split", [], '"yes" if value else "no"'),
    "hold": ("", '''    if text not in ("yes", "no"):
        raise CommandError("bad_yesno", text)
    value = text == "yes"
''', "cust.hold", [], '"yes" if value else "no"'),
    "po": ("MAX_LEN = 40\n", '''    if len(text) > MAX_LEN or any(ord(c) < 32 for c in text):
        raise CommandError("bad_value", text)
    value = "" if text == "-" else text
''', "cust.po", [], "output.dash(value)"),
    "name": ("MAX_LEN = 60\n", '''    if not text.strip() or len(text) > MAX_LEN:
        raise CommandError("bad_value", text)
    value = text
''', "cust.name", [], "output.quote(value)"),
    "email": ("MAX_LEN = 60\n", '''    if text == "-":
        value = ""
    elif "@" not in text or len(text) > MAX_LEN:
        raise CommandError("bad_value", text)
    else:
        value = text
''', "cust.email", [], "output.dash(value)"),
    "note": ("MAX_LEN = 80\n", '''    if len(text) > MAX_LEN:
        raise CommandError("bad_value", text)
    value = "" if text == "-" else text
''', "cust.note", [], "output.dash(value)"),
}

SET_TMPL = '''"""set @field@: change the @field@ of a customer."""
@imports@from errors import CommandError
@consts@

def show(value):
    return @shown@


def check(w, cust, text):
    """The new value for TEXT, or an error."""
@body@    return value


def cmd_set_@field@(w, cmd):
    cmd.allow()
    cust = customers.@lookup@(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = @attr@
    if value == old:
        w.out.emit("customer %s @field@ unchanged" % cust.id)
        return
    @attr@ = value
@audit@    w.out.emit("customer %s @field@ %s" % (cust.id, show(value)))
'''
SET_AUDIT = '    w.audit_add("set @field@", cust.id, show(old), show(value))\n'


def gen_setters():
    for field, (consts, body, attr, imps, shown) in SETTERS.items():
        loc = set(imps) | {"customers"}
        if "output." in shown:
            loc.add("output")
        imports = "".join("import %s\n" % i for i in sorted(loc))
        consts = "\n" + consts if consts else ""
        lookup = "get" if field == "note" else "open"
        audit = "" if field == "note" else SET_AUDIT.replace("@field@", field)
        write("set_%s.py" % field, fill(SET_TMPL, field=field, imports=imports, consts=consts,
                                        body=body, attr=attr, shown=shown, lookup=lookup,
                                        audit=audit))


# ------------------------------------------------------------------ reports
ORDERS_TMPL = '''"""Report @name@: @title@."""
import customers
import orders
import reportutil

NAME = "@name@"
TITLE = "@title@"


def key_of(w, order):
    return @key@


def value_of(order):
    return order.goods


def total_orders(w):
    """Number of orders a report of this kind covers."""
    return len(orders.live(w))


def run(w, cmd):
    cmd.allow("cust")
    _, want_cust = reportutil.filters(w, cmd)
    rows = {}
    for order in @source@:
        if want_cust and order.cust != want_cust:
            continue
        key = key_of(w, order)
        rows[key] = rows.get(key, 0) + value_of(order)
    reportutil.emit_groups(w, rows)


def describe():
    return "%s: %s" % (NAME, TITLE)
'''
ORDERS_REPORTS = [
    ("goods_region", "Goods value ordered per destination region", "customers.get(w, order.cust).region"),
    ("goods_tier", "Goods value ordered per customer tier", "customers.get(w, order.cust).tier"),
    ("goods_customer", "Goods value ordered per customer", "order.cust"),
]
SHIP_TMPL = '''"""Report @name@: @title@."""
import customers
import orders
import reportutil

NAME = "@name@"
TITLE = "@title@"


def key_of(shipment):
    return @key@


def value_of(shipment):
    return @value@


def run(w, cmd):
    cmd.allow("wh", "cust")
    want_wh, want_cust = reportutil.filters(w, cmd)
    rows = {}
    for s in w.shipments:
        if want_wh and s.wh != want_wh:
            continue
        if want_cust and orders.find(w, s.order).cust != want_cust:
            continue
        amount = value_of(s)
        if amount == 0:
            continue
        rows[key_of(s)] = rows.get(key_of(s), 0) + amount
    reportutil.emit_groups(w, rows)


def describe():
    return "%s: %s" % (NAME, TITLE)
'''
SHIP_REPORTS = [
    ("freight_carrier", "Freight charged per carrier", "shipment.carrier", "shipment.freight"),
    ("freight_region", "Freight charged per destination region", "shipment.region", "shipment.freight"),
    ("duty_region", "Import duty charged per destination region", "shipment.region", "shipment.duty"),
]
LOT_TMPL = '''"""Report @name@: @title@."""
import reportutil
import skus
import stock

NAME = "@name@"
TITLE = "@title@"
KIND = "@kind@"


def key_of(lot):
    return @key@


def value_of(lot):
    return @value@


def run(w, cmd):
    cmd.allow("wh")
    want_wh, _ = reportutil.filters(w, cmd)
    rows = {}
    for lot in sorted(w.lots.values(), key=lambda x: x.id):
        if want_wh and lot.wh != want_wh:
            continue
        rows[key_of(lot)] = rows.get(key_of(lot), 0) + value_of(lot)
    reportutil.emit_groups(w, rows, KIND)


def describe():
    return "%s: %s" % (NAME, TITLE)
'''
LOT_REPORTS = [
    ("stock_wh", "Units on hand per warehouse", "lot.wh", "lot.qty", "units"),
    ("stock_cat", "Units on hand per category", "skus.category(lot.sku)", "lot.qty", "units"),
    ("value_wh", "Stock value at cost per warehouse", "lot.wh", "lot.qty * skus.cost(lot.sku)", "money"),
]

SPECIAL = {}
SPECIAL["low_stock"] = ("Slots at or below their reorder point", '''"""Report low_stock: Slots at or below their reorder point."""
import reportutil
import stock

NAME = "low_stock"
TITLE = "Slots at or below their reorder point"


def run(w, cmd):
    cmd.allow("wh")
    want_wh, _ = reportutil.filters(w, cmd)
    count = 0
    for wh, sku in sorted(w.by_slot):
        if want_wh and wh != want_wh:
            continue
        cat = stock.category_of(sku)
        have = stock.available(w, wh, sku)
        if cat.needs_reorder(have):
            w.out.emit("  %s %s available=%d reorder=%d" % (wh, sku, have, cat.REORDER))
            count += 1
    if not count:
        w.out.emit("  (none)")
''')
SPECIAL["expiring"] = ("Lots that expire within N days (default 7)", '''"""Report expiring: Lots that expire within N days (default 7)."""
import money
import reportutil

NAME = "expiring"
TITLE = "Lots that expire within N days (default 7)"


def run(w, cmd):
    cmd.allow("wh", "days")
    want_wh, _ = reportutil.filters(w, cmd)
    days = money.parse_int(cmd.opt("days", "7"), 0, 400)
    count = 0
    for lot in sorted(w.lots.values(), key=lambda x: (x.expiry is None, x.expiry, x.id)):
        if lot.expiry is None:
            continue
        if want_wh and lot.wh != want_wh:
            continue
        left = lot.expiry - w.day
        if 0 <= left <= days:
            w.out.emit("  %s %s %s qty=%d expiry=%d days_left=%d" % (
                lot.id, lot.wh, lot.sku, lot.qty, lot.expiry, left))
            count += 1
    if not count:
        w.out.emit("  (none)")
''')
SPECIAL["backorders"] = ("Units on backorder per sku", '''"""Report backorders: Units on backorder per sku."""
import orders
import reportutil

NAME = "backorders"
TITLE = "Units on backorder per sku"


def run(w, cmd):
    cmd.allow()
    rows = {}
    for order in orders.live(w):
        for line in order.lines:
            if line.backorder > 0:
                rows[line.sku] = rows.get(line.sku, 0) + line.backorder
    reportutil.emit_groups(w, rows, "units")
''')
SPECIAL["status"] = ("Orders per status", '''"""Report status: Orders per status."""
import orders
import reportutil

NAME = "status"
TITLE = "Orders per status"
ORDER = ("open", "partial", "backorder", "shipped", "cancelled")


def run(w, cmd):
    cmd.allow()
    rows = {}
    for order in orders.all_sorted(w):
        rows[order.status] = rows.get(order.status, 0) + 1
    reportutil.emit_groups(w, rows, "units", order=ORDER)
''')
SPECIAL["cancelled"] = ("Orders that were cancelled", '''"""Report cancelled: Orders that were cancelled."""
import money
import orders
import reportutil

NAME = "cancelled"
TITLE = "Orders that were cancelled"


def run(w, cmd):
    cmd.allow("cust")
    _, want_cust = reportutil.filters(w, cmd)
    count = 0
    for order in w.orders.values():
        if order.status != "cancelled":
            continue
        if want_cust and order.cust != want_cust:
            continue
        w.out.emit("  %s %s day %d goods %s" % (order.number, order.cust, order.day,
                                                money.fmt(order.goods)))
        count += 1
    w.out.emit("  %d cancelled" % count)
''')
SPECIAL["returns_cat"] = ("Units returned and restocked per category", '''"""Report returns_cat: Units returned and restocked per category."""
import reportutil
import skus

NAME = "returns_cat"
TITLE = "Units returned and restocked per category"


def run(w, cmd):
    cmd.allow("wh")
    want_wh, _ = reportutil.filters(w, cmd)
    rows = {}
    for m in w.moves:
        if m.kind != "return":
            continue
        if want_wh and m.wh != want_wh:
            continue
        key = skus.category(m.sku)
        rows[key] = rows.get(key, 0) + m.qty
    reportutil.emit_groups(w, rows, "units")
''')
SPECIAL["scrap_cat"] = ("Units scrapped, expired or written off per category", '''"""Report scrap_cat: Units scrapped, expired or written off per category."""
import reportutil
import skus

NAME = "scrap_cat"
TITLE = "Units scrapped, expired or written off per category"
KINDS = ("scrap", "expire")


def run(w, cmd):
    cmd.allow("wh")
    want_wh, _ = reportutil.filters(w, cmd)
    rows = {}
    for m in w.moves:
        if m.kind not in KINDS:
            continue
        if want_wh and m.wh != want_wh:
            continue
        key = skus.category(m.sku)
        rows[key] = rows.get(key, 0) + m.qty
    reportutil.emit_groups(w, rows, "units")
''')


def gen_reports():
    names = []
    for name, title, key in ORDERS_REPORTS:
        write("rpt_%s.py" % name, fill(ORDERS_TMPL, name=name, title=title, key=key,
                                       source="orders.live(w)"))
        names.append(name)
    for name, title, key, value in SHIP_REPORTS:
        write("rpt_%s.py" % name, fill(SHIP_TMPL, name=name, title=title, key=key, value=value))
        names.append(name)
    for name, title, key, value, kind in LOT_REPORTS:
        write("rpt_%s.py" % name, fill(LOT_TMPL, name=name, title=title, key=key, value=value,
                                       kind=kind))
        names.append(name)
    for name, (title, text) in SPECIAL.items():
        write("rpt_%s.py" % name, text)
        names.append(name)
    names.sort()
    body = ['"""The report registry: every report module by name."""', ""]
    for n in names:
        body.append("import rpt_%s" % n)
    body += ["", "MODULES = {"]
    for n in names:
        body.append('    "%s": rpt_%s,' % (n, n))
    body += ["}", "", "", "def known(name):", "    return name in MODULES", "", "",
             "def get(name):", "    return MODULES[name]", "", "",
             "def names():", "    return sorted(MODULES)", ""]
    write("reports.py", "\n".join(body))


# ------------------------------------------------------------------ command table
COMMANDS = [
    (("today",), "clockcmd", "cmd_today", "today"),
    (("tick",), "clockcmd", "cmd_tick", "tick DAYS"),
    (("customer", "add"), "customers", "cmd_add", "customer add ID REGION [tier=TIER] [name=TEXT]"),
    (("customer", "show"), "customers", "cmd_show", "customer show ID"),
    (("customer", "list"), "customers", "cmd_list", "customer list [tier=TIER] [region=REGION] [status=active|closed]"),
    (("customer", "close"), "customers", "cmd_close", "customer close ID"),
    (("customer", "history"), "customers", "cmd_history", "customer history ID"),
    (("sku", "list"), "catalog", "cmd_sku_list", "sku list"),
    (("sku", "show"), "catalog", "cmd_sku_show", "sku show SKU"),
    (("warehouse", "list"), "catalog", "cmd_warehouse_list", "warehouse list"),
    (("warehouse", "show"), "catalog", "cmd_warehouse_show", "warehouse show WAREHOUSE"),
    (("category", "list"), "catalog", "cmd_category_list", "category list"),
    (("category", "show"), "catalog", "cmd_category_show", "category show CATEGORY"),
    (("carrier", "list"), "catalog", "cmd_carrier_list", "carrier list"),
    (("carrier", "show"), "catalog", "cmd_carrier_show", "carrier show CARRIER"),
    (("region", "list"), "catalog", "cmd_region_list", "region list"),
    (("region", "show"), "catalog", "cmd_region_show", "region show REGION"),
    (("tier", "list"), "tiers", "cmd_list", "tier list"),
    (("receive",), "receiving", "cmd_receive", "receive WAREHOUSE SKU UNITS [exp=DAY]"),
    (("stock",), "stockcmd", "cmd_stock", "stock [WAREHOUSE] [sku=SKU]"),
    (("adjust",), "adjust", "cmd_adjust", "adjust WAREHOUSE SKU DELTA"),
    (("transfer",), "transfers", "cmd_transfer", "transfer FROM TO SKU UNITS"),
    (("expire",), "expiry", "cmd_expire", "expire [WAREHOUSE]"),
    (("replenish",), "replenish", "cmd_replenish", "replenish [WAREHOUSE]"),
    (("order", "add"), "orders", "cmd_add", "order add CUSTOMER SKU:QTY... [ref=TEXT]"),
    (("order", "show"), "orders", "cmd_show", "order show NUMBER"),
    (("order", "list"), "orders", "cmd_list", "order list [CUSTOMER] [state=STATE]"),
    (("order", "cancel"), "orders", "cmd_cancel", "order cancel NUMBER"),
    (("backorder", "run"), "backorders", "cmd_run", "backorder run"),
    (("ship",), "shipping", "cmd_ship", "ship NUMBER [at=HOUR] [carrier=CARRIER]"),
    (("return",), "returns", "cmd_return", "return NUMBER SKU QTY [cond=good|damaged]"),
    (("ledger",), "stockcmd", "cmd_ledger", "ledger [WAREHOUSE] [kind=KIND] [sku=SKU]"),
    (("audit",), "audit", "cmd_audit", "audit [COUNT] [action=TEXT] [subject=TEXT]"),
    (("export",), "export", "cmd_export", "export KIND FORMAT"),
    (("report",), "reportcmd", "cmd_report", "report NAME [ARGS]"),
]
for _field, _usage in (("region", "REGION"), ("tier", "TIER"), ("carrier", "CARRIER|auto"),
                       ("split", "yes|no"), ("hold", "yes|no"), ("po", "TEXT"),
                       ("name", "TEXT"), ("email", "ADDRESS"), ("note", "TEXT")):
    COMMANDS.append((("set", _field), "set_" + _field, "cmd_set_" + _field,
                     "set %s ID %s" % (_field, _usage)))
COMMANDS.append((("help",), "helptext", "cmd_help", "help [COMMAND]"))


def gen_cmdtable():
    mods = sorted(set(c[1] for c in COMMANDS))
    body = ['"""The command table: command words, handler and usage line."""', ""]
    for m in mods:
        body.append("import %s" % m)
    body += ["from errors import CommandError", "", "COMMANDS = {"]
    for words, mod, fn, usage in COMMANDS:
        body.append("    %r: (%s.%s, %r)," % (words, mod, fn, usage))
    body += ["}", "", "", "def resolve(cmd):",
             "    words = cmd.words",
             "    for n in (2, 1):",
             "        entry = COMMANDS.get(tuple(words[:n]))",
             "        if entry is not None:",
             "            cmd.name = \" \".join(words[:n])",
             "            cmd.args = words[n:]",
             "            cmd.usage = entry[1]",
             "            return entry[0]",
             "    raise CommandError(\"unknown_command\", words[0])",
             "", "", "def listing():",
             "    return [(words, COMMANDS[words][1]) for words in sorted(COMMANDS)]", ""]
    write("cmdtable.py", "\n".join(body))


# ------------------------------------------------------------------ README
def day_names(days):
    return ",".join(NAMES[d] for d in days)


def readme_tables():
    t = {}
    rows = ["| code | zone | cut-off hour | dispatches on | capacity | max haz | stores groups | pick fee | pack fee |",
            "|---|---|---|---|---|---|---|---|---|"]
    for code, name, zone, cutoff, od, cap, haz, acc, pick, pack in WAREHOUSES:
        rows.append("| %s | %d | %d | %s | %d | %d | %s | %d | %d |" % (
            code, zone, cutoff, day_names(od), cap, haz, ", ".join(acc), pick, pack))
    t["WAREHOUSES"] = "\n".join(rows)
    rows = ["| code | group | pack | unit g | shelf days | margin days | max per line | reorder at | haz | return days | returns restocked |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for code, name, group, pack, ug, shelf, margin, ml, ro, haz, win, restock in CATEGORIES:
        rows.append("| %s | %s | %d | %d | %s | %d | %s | %s | %d | %s | %s |" % (
            code, group, pack, ug, shelf or "-", margin, ml or "no limit", ro or "-", haz,
            win or "no returns", "yes" if restock == "always" else "never"))
    t["CATEGORIES"] = "\n".join(rows)
    rows = ["| code | base | step g | per step | parcel g | total limit g | minimum | zone bp | fuel bp | transit | haz max | serves |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for code, name, base, sg, sc, mg, mt, minc, zbp, fbp, tb, ts, haz, cov in CARRIERS:
        rows.append("| %s | %d | %d | %d | %s | %s | %d | %d | %d | %d + 1 per %d zones | %d | %s |" % (
            code, base, sg, sc, mg or "none", mt or "none", minc, zbp, fbp, tb, ts, haz,
            "all" if cov is None else ", ".join(cov)))
    t["CARRIERS"] = "\n".join(rows)
    rows = ["| code | zone | no delivery on | haz ban level | duty free up to | duty bp | customs days | remote fee |",
            "|---|---|---|---|---|---|---|---|"]
    for code, name, zone, we, ban, free, bp, cd, remote in REGIONS:
        rows.append("| %s | %d | %s | %d | %d | %d | %d | %d |" % (
            code, zone, day_names(we), ban, free, bp, cd, remote))
    t["REGIONS"] = "\n".join(rows)
    rows = ["| sku | category | cost | price |", "|---|---|---|---|"]
    for code, cat, cost, price, name in SKUS:
        rows.append("| %s | %s | %d | %d |" % (code, cat, cost, price))
    t["SKUS"] = "\n".join(rows)
    return t


def gen_readme():
    with open(os.path.join(CORE, "README.md")) as f:
        text = f.read()
    for key, value in readme_tables().items():
        text = text.replace("{{%s}}" % key, value)
    assert "{{" not in text
    with open(os.path.join(GOLD, "README.md"), "w") as f:
        f.write(text)


def main():
    if os.path.isdir(GOLD):
        shutil.rmtree(GOLD)
    os.makedirs(GOLD)
    for name in sorted(os.listdir(CORE)):
        if name.endswith(".py") or name == "build.sh":
            shutil.copy(os.path.join(CORE, name), os.path.join(GOLD, name))
    gen_warehouses()
    gen_categories()
    gen_skus()
    gen_carriers()
    gen_regions()
    gen_setters()
    gen_reports()
    gen_cmdtable()
    gen_readme()
    print("generated")


if __name__ == "__main__":
    main()
