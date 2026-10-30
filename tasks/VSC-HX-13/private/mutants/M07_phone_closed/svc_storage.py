# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Service storage: Object storage, billed per block of 1000 GB-h."""
import money

CODE = "storage"
LABEL = "Object storage"
UNIT = "GB-h"
BLOCK = 1000
MODE = "ceil"
MIN_CHARGE = 0
UNITS_CAP = 1000000
PLAN_ORDER = ("free", "starter", "team", "business", "enterprise")
TIERS = ((100, 12), (400, 9), (None, 6))
ALLOW = {'free': 2000, 'starter': 8000, 'team': 24000, 'business': 80000, 'enterprise': 300000}
PROFILES = {'light': 30000, 'typical': 300000, 'heavy': 1000000}


def blocks_for(billable):
    """Blocks for BILLABLE units."""
    return money.ceil_div(billable, BLOCK)


def tier_spans(blocks):
    """Price spans (first block, last block, price) for BLOCKS blocks."""
    spans = []
    used = 0
    for upto, price in TIERS:
        top = blocks if upto is None else min(blocks, upto)
        if top > used:
            spans.append((used + 1, top, price))
            used = top
    return spans


def rate(units, allow):
    """Charge in base cents for UNITS with ALLOW units free."""
    billable = units - allow
    if billable <= 0:
        return 0
    total = 0
    for first, last, price in tier_spans(blocks_for(billable)):
        total += (last - first + 1) * price
    return max(total, MIN_CHARGE)


def quote(units, plan):
    return rate(units, ALLOW[plan])


def explain(units, plan):
    allow = ALLOW[plan]
    billable = max(0, units - allow)
    out = ["units=%d allowance=%d billable=%d blocks=%d" % (units, allow, billable, blocks_for(billable))]
    for first, last, price in tier_spans(blocks_for(billable)):
        out.append("blocks %d-%d x %d" % (first, last, price))
    return out


def rate_card():
    """The price list as rows (first block, last block or None, price)."""
    rows = []
    prev = 0
    for upto, price in TIERS:
        rows.append((prev + 1, upto, price))
        if upto is not None:
            prev = upto
    return rows


def allowance(plan):
    return ALLOW[plan]


def free_blocks(plan):
    return ALLOW[plan] // BLOCK


def compare(units):
    """(charge, plan) under every plan, cheapest first."""
    rows = [(rate(units, ALLOW[p]), p) for p in PLAN_ORDER]
    rows.sort(key=lambda row: (row[0], PLAN_ORDER.index(row[1])))
    return rows


def marginal(units, plan):
    """Price in base cents of the next block after UNITS under PLAN."""
    billable = max(0, units - ALLOW[plan])
    block_no = blocks_for(billable) + 1
    for first, last, price in rate_card():
        if last is None or block_no <= last:
            return price
    return TIERS[-1][1]


def validate_units(units):
    return 0 < units <= UNITS_CAP


def describe():
    return "%s block=%d unit=%s mode=%s" % (CODE, BLOCK, UNIT, MODE)


def summary():
    return {
        "code": CODE,
        "label": LABEL,
        "unit": UNIT,
        "block": BLOCK,
        "mode": MODE,
        "tiers": len(TIERS),
        "min": MIN_CHARGE,
    }


def savings(units, plan_from, plan_to):
    """Base cents saved on UNITS by moving from PLAN_FROM to PLAN_TO."""
    return rate(units, ALLOW[plan_from]) - rate(units, ALLOW[plan_to])


def is_flat():
    return len(TIERS) == 1


def top_price():
    return TIERS[-1][1]


def profile_units(name):
    return PROFILES[name]


def profile_cost(plan, name):
    """Charge in base cents of the named usage profile under PLAN."""
    return rate(PROFILES[name], ALLOW[plan])


def profile_table():
    """Rows (plan, light, typical, heavy) of base-cent charges."""
    rows = []
    for plan in PLAN_ORDER:
        rows.append((plan, profile_cost(plan, "light"), profile_cost(plan, "typical"),
                     profile_cost(plan, "heavy")))
    return rows


def crossover(plan_a, plan_b, fee_a, fee_b, limit=None):
    """First unit count (a whole number of blocks) at which PLAN_B plus its
    fee costs no more than PLAN_A plus its fee, or None up to LIMIT."""
    limit = UNITS_CAP if limit is None else limit
    units = BLOCK
    while units <= limit:
        if fee_b + rate(units, ALLOW[plan_b]) <= fee_a + rate(units, ALLOW[plan_a]):
            return units
        units += BLOCK
    return None


def effective_ppm(units, plan):
    """Average base cents per unit, in millionths."""
    if units <= 0:
        return 0
    return money.div_half_up(rate(units, ALLOW[plan]) * 1000000, units)
