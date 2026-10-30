# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Category electronics: Electronics, group dry."""
import money
from errors import CommandError

CODE = "electronics"
NAME = "Electronics"
GROUP = "dry"
PACK = 4
UNIT_G = 350
SHELF = 0
MARGIN = 0
MAX_LINE = 200
REORDER = 20
HAZ = 1
RETURN_WINDOW = 14
RESTOCK = "always"


def round_receive(units):
    """Units booked for a receipt of UNITS."""
    return money.ceil_div(units, PACK) * PACK


def check_line(qty):
    """Refuse an order line of QTY units that breaks the category's rules."""
    if MAX_LINE and qty > MAX_LINE:
        raise CommandError("line_limit", CODE, MAX_LINE, qty)
    return qty


def expiry_for(day, given):
    """Last sellable day of a lot received on DAY, or None."""
    if given is not None:
        raise CommandError("bad_option", "exp")
    if SHELF == 0:
        return None
    return day + SHELF


def is_expired(expiry, day):
    return expiry is not None and day > expiry


def sellable(expiry, day):
    """True if a lot with EXPIRY may be allocated on DAY."""
    return expiry is None or expiry - day >= MARGIN


def needs_reorder(available):
    return REORDER > 0 and available <= REORDER


def return_ok(days):
    """True if goods shipped DAYS days ago may still be returned."""
    return RETURN_WINDOW > 0 and days <= RETURN_WINDOW


def disposition(cond):
    """What happens to returned goods in condition COND."""
    if cond == "damaged" or RESTOCK == "never":
        return "scrap"
    return "restock"


def weight(qty):
    """Shipping weight in grams of QTY units."""
    return qty * UNIT_G


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
