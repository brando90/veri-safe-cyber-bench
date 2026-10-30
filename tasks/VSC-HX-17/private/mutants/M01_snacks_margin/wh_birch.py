# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Warehouse birch: Birch Depot."""
import money
import timeutil

CODE = "birch"
NAME = "Birch Depot"
ZONE = 5
CUTOFF = 15
OPEN_DAYS = (0, 1, 2, 3, 4)
CAPACITY = 4000
HAZ_MAX = 3
ACCEPTS = ('dry', 'haz')
PICK_FEE = 45
PACK_FEE = 110


def cutoff_on(day):
    """The cut-off hour that applies on DAY."""
    return CUTOFF


def ship_day(day, hour):
    """First dispatch day for goods ready at HOUR on DAY."""
    first = day if hour < cutoff_on(day) else day + 1
    return timeutil.next_open(first, OPEN_DAYS)


def limit():
    """Most units the warehouse may hold."""
    return CAPACITY


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
    return abs(ZONE - region_zone)


def handling(lines, units):
    """Handling fee in cents for a shipment of LINES lines and UNITS units."""
    return PICK_FEE * lines + PACK_FEE


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
