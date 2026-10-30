# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Carrier swift: Swift Parcel."""
import money

CODE = "swift"
NAME = "Swift Parcel"
BASE = 450
STEP_G = 500
STEP_COST = 60
MAX_G = 20000
MAX_TOTAL = 0
MIN_CHARGE = 600
ZONE_BP = 300
FUEL_BP = 800
TRANSIT_BASE = 1
TRANSIT_STEP = 3
HAZ_MAX = 1
COVERS = None


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
    sub = rate(weight)
    zone = money.pct(sub, distance * ZONE_BP)
    fuel = money.pct(sub + zone, FUEL_BP)
    return max(sub + zone + fuel, MIN_CHARGE)


def transit(distance):
    """Days in transit over DISTANCE zones."""
    return TRANSIT_BASE + distance // TRANSIT_STEP


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
