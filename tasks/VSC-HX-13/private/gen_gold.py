#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Deterministic generator of the repetitive part of private/gold: the service
rating modules, tax regions, coupon kinds, currencies, customer setters and
reports, plus their registries and the command table.  The result is committed
as plain source in gold/; this script is not part of the public tree."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = os.path.join(HERE, "gold")
HDR = "# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.\n"
PLANS = ("free", "starter", "team", "business", "enterprise")
MULT = (1, 4, 12, 40, 150)


def write(name, text):
    with open(os.path.join(GOLD, name), "w") as f:
        f.write(HDR + text.lstrip("\n"))


# ------------------------------------------------------------------ services
# code, label, unit, block, tiers, min charge, mode, allowance base
SERVICES = [
    ("storage", "Object storage", "GB-h", 1000, ((100, 12), (400, 9), (None, 6)), 0, "ceil", 2000),
    ("egress", "Outbound transfer", "GB", 10, ((50, 40), (200, 32), (None, 25)), 0, "ceil", 20),
    ("compute", "Compute time", "CPU-min", 60, ((20, 95), (None, 80)), 0, "ceil", 120),
    ("requests", "API requests", "req", 1000, ((None, 15),), 0, "ceil", 5000),
    ("sms", "SMS messages", "msg", 100, ((10, 70), (None, 55)), 0, "ceil", 100),
    ("voice", "Voice minutes", "min", 5, ((None, 45),), 0, "whole", 0),
    ("email", "Transactional email", "msg", 500, ((20, 30), (None, 22)), 0, "ceil", 1000),
    ("logs", "Log retention", "MB", 250, ((None, 7),), 0, "ceil", 1000),
    ("backup", "Backup storage", "GB-h", 500, ((60, 18), (200, 14), (None, 10)), 0, "ceil", 500),
    ("cdn", "CDN delivery", "GB", 5, ((100, 22), (None, 17)), 0, "ceil", 10),
    ("dns", "DNS queries", "kq", 100, ((None, 4),), 100, "ceil", 0),
    ("queue", "Message queue", "kmsg", 50, ((30, 16), (120, 13), (None, 10)), 0, "ceil", 100),
    ("search", "Search index", "kdoc", 20, ((40, 35), (None, 28)), 0, "ceil", 40),
    ("cache", "Cache memory", "MB-h", 128, ((None, 11),), 50, "ceil", 256),
    ("vault", "Secrets vault", "secret", 10, ((None, 60),), 0, "ceil", 10),
    ("metrics", "Metric series", "series", 100, ((25, 20), (None, 14)), 0, "ceil", 200),
    ("ocr", "OCR pages", "page", 10, ((None, 120),), 0, "whole", 0),
    ("geocode", "Geocoding", "lookup", 250, ((None, 19),), 0, "whole", 250),
]

SVC_TMPL = '''"""Service {code}: {label}, billed per block of {block} {unit}."""
import money

CODE = "{code}"
LABEL = "{label}"
UNIT = "{unit}"
BLOCK = {block}
MODE = "{mode}"
MIN_CHARGE = {minc}
UNITS_CAP = 1000000
PLAN_ORDER = ("free", "starter", "team", "business", "enterprise")
TIERS = {tiers}
ALLOW = {allow}
PROFILES = {profiles}


def blocks_for(billable):
    """Blocks for BILLABLE units."""
    return {blocks_expr}


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
    return {{
        "code": CODE,
        "label": LABEL,
        "unit": UNIT,
        "block": BLOCK,
        "mode": MODE,
        "tiers": len(TIERS),
        "min": MIN_CHARGE,
    }}


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
'''


def gen_services():
    for code, label, unit, block, tiers, minc, mode, base in SERVICES:
        allow = {p: base * m for p, m in zip(PLANS, MULT)}
        expr = "money.ceil_div(billable, BLOCK)" if mode == "ceil" else "billable // BLOCK"
        write("svc_%s.py" % code, SVC_TMPL.format(
            code=code, label=label, unit=unit, block=block, mode=mode, minc=minc,
            tiers=repr(tiers), allow=repr(allow), blocks_expr=expr,
            profiles=repr({"light": min(block * 30, 1000000), "typical": min(block * 300, 1000000),
                           "heavy": min(block * 3000, 1000000)})))
    names = [s[0] for s in SERVICES]
    body = ['"""The service registry: every rating module by code."""', ""]
    for n in names:
        body.append("import svc_%s" % n)
    body += ["", "MODULES = {"]
    for n in names:
        body.append('    "%s": svc_%s,' % (n, n))
    body += ["}", "", "", "def known(code):", "    return code in MODULES", "", "",
             "def get(code):", "    return MODULES[code]", "", "",
             "def codes():", "    return sorted(MODULES)", ""]
    write("services.py", "\n".join(body))


# ------------------------------------------------------------------ tax regions
# code, name, rate bp, taxable kinds, parts (or None)
ALL_KINDS = ("adjust", "fee", "usage")
TAXES = [
    ("ca", "California sales tax", 725, ALL_KINDS, None),
    ("ny", "New York sales tax", 850, ALL_KINDS, (400, 450)),
    ("tx", "Texas sales tax", 625, ALL_KINDS, None),
    ("wa", "Washington sales tax", 1010, ALL_KINDS, (650, 360)),
    ("de", "German VAT", 1900, ALL_KINDS, None),
    ("fr", "French VAT", 2000, ALL_KINDS, None),
    ("es", "Spanish VAT", 2100, ALL_KINDS, None),
    ("uk", "UK VAT", 2000, ALL_KINDS, None),
    ("jp", "Japan consumption tax", 1000, ("usage",), None),
    ("on", "Ontario HST", 1300, ALL_KINDS, None),
    ("ch", "Swiss VAT", 810, ("adjust", "fee"), None),
]

TAX_TMPL = '''"""Tax region {code}: {name}."""
import money

CODE = "{code}"
NAME = "{name}"
RATE_BP = {rate}
TAXABLE = frozenset({kinds})
{parts_line}

def taxable_sum(lines):
    return sum(line.amount for line in lines if line.kind in TAXABLE)


def compute(lines, discount, exempt):
    if exempt:
        return 0
    base = taxable_sum(lines) - discount
    if base <= 0:
        return 0
    return {ret}


def describe():
    return "%s %d bp" % (NAME, RATE_BP)


def breakdown(lines):
    """Taxable amount per line kind, before any discount."""
    out = {{}}
    for line in lines:
        if line.kind in TAXABLE:
            out[line.kind] = out.get(line.kind, 0) + line.amount
    return out


def gross_to_net(total):
    """The net amount inside a tax-inclusive TOTAL."""
    return money.div_half_up(total * 10000, 10000 + RATE_BP)


def tax_inside(total):
    return total - gross_to_net(total)


def kinds_text():
    return ",".join(sorted(TAXABLE))


def rate_text():
    return money.fmt(RATE_BP, 2) + "%"


def explain(lines, discount, exempt):
    out = ["region %s %s" % (CODE, rate_text())]
    for kind, amount in sorted(breakdown(lines).items()):
        out.append("  %s %d" % (kind, amount))
    out.append("  discount %d" % discount)
    out.append("  exempt %s" % ("yes" if exempt else "no"))
    out.append("  tax %d" % compute(lines, discount, exempt))
    return out


def applies_to(kind):
    return kind in TAXABLE


def is_zero_rated():
    return RATE_BP == 0
'''


def gen_taxes():
    for code, name, rate, kinds, parts in TAXES:
        if parts:
            parts_line = "PARTS = %r\n" % (parts,)
            ret = "money.pct(base, PARTS[0]) + money.pct(base, PARTS[1])"
        else:
            parts_line = ""
            ret = "money.pct(base, RATE_BP)"
        write("tax_%s.py" % code, TAX_TMPL.format(
            code=code, name=name, rate=rate, kinds=repr(tuple(sorted(kinds))),
            parts_line=parts_line, ret=ret))
    names = [t[0] for t in TAXES]
    body = ['"""The tax registry: every region module by code."""', "",
            "import money  # noqa: F401" if False else ""]
    body = ['"""The tax registry: every region module by code."""', ""]
    for n in names:
        body.append("import tax_%s" % n)
    body += ["", "MODULES = {"]
    for n in names:
        body.append('    "%s": tax_%s,' % (n, n))
    body += ["}", "", "", "def known(code):", "    return code in MODULES", "", "",
             "def get(code):", "    return MODULES[code]", "", "",
             "def codes():", "    return sorted(MODULES)", "", "",
             "def compute(region, lines, discount, exempt):",
             "    return MODULES[region].compute(lines, discount, exempt)", ""]
    write("taxes.py", "\n".join(body))


# ------------------------------------------------------------------ coupon kinds
DISC_HEAD = '''"""Coupon kind {name}: {what}."""
import money

NAME = "{name}"
DEFAULT_N = {dn}
'''
PCT_VALIDATE = '''

def validate(text, exp):
    return money.parse_int(text, 1, 100)
'''
FIXED_VALIDATE = '''

def validate(text, exp):
    return money.parse(text, exp)
'''
TARGETS = {"pct_all": "all", "pct_fee": "fee", "pct_usage": "usage", "fixed_all": "all",
           "fixed_fee": "fee", "fixed_usage": "usage", "first_periods": "all", "volume": "usage"}
DISC_TAIL = '''

def describe(cp):
    return "%s value=%d" % (NAME, cp.value)


def preview(ctx, cp):
    """What the coupon would take off a CTX invoice, never above its subtotal."""
    return max(0, min(amount(ctx, cp), ctx.subtotal))


def targets():
    return TARGET


def is_percentage():
    return NAME.startswith(("pct", "first", "volume"))


def limit_text(cp):
    if cp.until is None:
        return "no end day"
    return "starts on or before day %d" % cp.until
'''
DISCOUNTS = [
    ("pct_all", "a percentage off the whole subtotal", 0, PCT_VALIDATE,
     "    return money.pct(ctx.subtotal, cp.value * 100)"),
    ("pct_fee", "a percentage off the plan fee lines", 0, PCT_VALIDATE,
     "    return money.pct(ctx.fee, cp.value * 100)"),
    ("pct_usage", "a percentage off the metered usage lines", 0, PCT_VALIDATE,
     "    return money.pct(ctx.usage, cp.value * 100)"),
    ("fixed_all", "a fixed amount off the whole subtotal", 0, FIXED_VALIDATE,
     "    return min(cp.value, ctx.subtotal)"),
    ("fixed_fee", "a fixed amount off the plan fee lines", 0, FIXED_VALIDATE,
     "    return min(cp.value, ctx.fee)"),
    ("fixed_usage", "a fixed amount off the metered usage lines", 0, FIXED_VALIDATE,
     "    return min(cp.value, ctx.usage)"),
    ("first_periods", "a percentage off the subtotal for the first invoices only", 3, PCT_VALIDATE,
     "    if cp.used >= cp.n:\n        return 0\n    return money.pct(ctx.subtotal, cp.value * 100)"),
    ("volume", "a volume rebate on usage, capped by the coupon percentage", 0, PCT_VALIDATE,
     "    for need, rebate in THRESHOLDS:\n"
     "        if ctx.usage >= need * 10 ** ctx.exp:\n"
     "            return money.pct(ctx.usage, min(rebate, cp.value) * 100)\n"
     "    return 0"),
]


def gen_discounts():
    for name, what, dn, validate, body in DISCOUNTS:
        text = DISC_HEAD.format(name=name, what=what, dn=dn)
        if name == "volume":
            text += "THRESHOLDS = ((200, 15), (100, 10), (50, 5))\n"
        text += "TARGET = %r\n" % TARGETS[name]
        text += validate
        text += "\n\ndef amount(ctx, cp):\n" + body + "\n"
        text += DISC_TAIL
        write("disc_%s.py" % name, text)
    names = [d[0] for d in DISCOUNTS]
    body = ['"""The coupon registry: every coupon kind by name."""', ""]
    for n in names:
        body.append("import disc_%s" % n)
    body += ["", "MODULES = {"]
    for n in names:
        body.append('    "%s": disc_%s,' % (n, n))
    body += ["}", "", "", "def known(kind):", "    return kind in MODULES", "", "",
             "def get(kind):", "    return MODULES[kind]", "", "",
             "def kinds():", "    return sorted(MODULES)", ""]
    write("discounts.py", "\n".join(body))


# ------------------------------------------------------------------ currencies
CURRENCIES = [
    ("USD", "US dollar", 2, 1000000, 200),
    ("EUR", "Euro", 2, 920000, 180),
    ("GBP", "Pound sterling", 2, 790000, 150),
    ("JPY", "Japanese yen", 0, 1500000, 300),
    ("KWD", "Kuwaiti dinar", 3, 3100000, 600),
    ("CAD", "Canadian dollar", 2, 1350000, 250),
    ("CHF", "Swiss franc", 2, 900000, 175),
    ("INR", "Indian rupee", 2, 83000000, 5000),
]

CUR_TMPL = '''"""Currency {code}: {name}, {exp} decimals."""
import money

CODE = "{code}"
NAME = "{name}"
EXP = {exp}
RATE_PPM = {rate}
LATE_MIN = {late}


def from_base(cents):
    return {conv}


def to_base(minor):
    return money.div_half_up(minor * 1000000, RATE_PPM)


def text(amount):
    return money.fmt(amount, EXP)


def display(amount):
    return "%s %s" % (CODE, text(amount))


def minor_per_major():
    return 10 ** EXP


def rate_text():
    return money.fmt(RATE_PPM, 6)


def late_floor_text():
    return text(LATE_MIN)


def round_trip_gap(cents):
    """Base cents lost by converting CENTS out and back."""
    return cents - to_base(from_base(cents))


def whole_units(amount):
    return amount // minor_per_major()


def fraction(amount):
    return amount % minor_per_major()


def describe():
    return "%s exp=%d late_min=%s" % (CODE, EXP, late_floor_text())
'''


def gen_currencies():
    for code, name, exp, rate, late in CURRENCIES:
        conv = "(cents * RATE_PPM + 500000) // 1000000"
        write("cur_%s.py" % code.lower(), CUR_TMPL.format(
            code=code, name=name, exp=exp, rate=rate, late=late, conv=conv))
    names = [c[0].lower() for c in CURRENCIES]
    body = ['"""The currency registry: every currency module by code."""', "", "import money", ""]
    for n in names:
        body.append("import cur_%s" % n)
    body += ["", "MODULES = {"]
    for n in names:
        body.append('    "%s": cur_%s,' % (n.upper(), n))
    body += ["}", "", "", "def known(code):", "    return code in MODULES", "", "",
             "def get(code):", "    return MODULES[code]", "", "",
             "def codes():", "    return sorted(MODULES)", "", "",
             "def money_text(cur, amount):", "    return money.fmt(amount, cur.EXP)", "", "",
             "def base_text(cents):", "    return money.fmt(cents, 2) + \" USD\"", ""]
    write("currencies.py", "\n".join(body))


# ------------------------------------------------------------------ setters
SETTERS = {
    "region": ("", '''    if not taxes.known(text):
        raise CommandError("unknown_region", text)
    value = text
''', "cust.region", ["taxes"]),
    "currency": ("", '''    if not currencies.known(text):
        raise CommandError("unknown_currency", text)
    if w.by_cust.get(cust.id) or cust.credit:
        raise CommandError("has_invoices", cust.id)
    value = text
''', "cust.currency", ["currencies"]),
    "terms": ("MIN_DAYS = 1\nMAX_DAYS = 120\n", '''    value = money.parse_int(text, MIN_DAYS, MAX_DAYS)
''', "cust.terms", ["money"]),
    "po": ("MAX_LEN = 40\n", '''    if len(text) > MAX_LEN or any(ord(c) < 32 for c in text):
        raise CommandError("bad_value", text)
    value = "" if text == "-" else text
''', "cust.po", []),
    "exempt": ("", '''    if text not in ("yes", "no"):
        raise CommandError("bad_yesno", text)
    value = text == "yes"
''', "cust.exempt", []),
    "name": ("MAX_LEN = 60\n", '''    if not text.strip() or len(text) > MAX_LEN:
        raise CommandError("bad_value", text)
    value = text
''', "cust.name", []),
    "email": ("MAX_LEN = 60\n", '''    if text == "-":
        value = ""
    elif "@" not in text or len(text) > MAX_LEN:
        raise CommandError("bad_value", text)
    else:
        value = text
''', "cust.email", []),
    "phone": ("PATTERN = r\"[0-9+() -]{3,20}\"\n", '''    if text == "-":
        value = ""
    elif not re.fullmatch(PATTERN, text):
        raise CommandError("bad_value", text)
    else:
        value = text
''', "cust.phone", ["re"]),
    "note": ("MAX_LEN = 80\n", '''    if len(text) > MAX_LEN:
        raise CommandError("bad_value", text)
    value = "" if text == "-" else text
''', "cust.note", []),
}

SET_TMPL = '''"""set {field}: change the {field} of a customer."""
{imports}from errors import CommandError
{consts}

def check(w, cust, text):
    """The new value for TEXT, or an error."""
{body}    return value


def cmd_set_{field}(w, cmd):
    cust = customers.open(w, cmd.arg(0))
    value = check(w, cust, cmd.arg(1))
    old = {attr}
    if value == old:
        w.out.emit("customer %s {field} unchanged" % cust.id)
        return
    {attr} = value
    w.audit_add("set {field}", cust.id, old, value)
    w.out.emit("customer %s {field} %s" % (cust.id, {shown}))
'''


def gen_setters():
    for field, (consts, body, attr, imps) in SETTERS.items():
        shown = {"exempt": '"yes" if value else "no"', "name": "output.quote(value)"}.get(
            field, "output.dash(value)" if field in ("po", "email", "phone", "note") else "value")
        loc = set(i for i in imps if i != "re") | {"customers"}
        if "output." in shown:
            loc.add("output")
        imports = ("import re\n\n" if "re" in imps else "") + "".join(
            "import %s\n" % i for i in sorted(loc))
        consts = "\n" + consts if consts else ""
        text = SET_TMPL.format(field=field, imports=imports, consts=consts, body=body,
                               attr=attr, shown=shown)
        write("set_%s.py" % field, text)


# ------------------------------------------------------------------ reports
GROUPED_TMPL = '''"""Report {name}: {title}."""
import invoice
import reportutil

NAME = "{name}"
TITLE = "{title}"


def key_of(inv):
    return {key}


def value_of(inv):
    return {value}


def run(w, cmd):
    cmd.allow("cur", "cust")
    want_cur, want_cust = reportutil.filters(w, cmd)
    rows = {{}}
    for inv in {source}:
        if want_cur and inv.currency != want_cur:
            continue
        if want_cust and inv.cust != want_cust:
            continue
        amount = value_of(inv)
        if amount == 0:
            continue
        k = (key_of(inv), inv.currency)
        rows[k] = rows.get(k, 0) + amount
    reportutil.emit_groups(w, rows)


def describe():
    return "%s: %s" % (NAME, TITLE)
'''
GROUPED = [
    ("rev_region", "Net revenue per tax region", "inv.region", "inv.subtotal - inv.discount + inv.late"),
    ("rev_plan", "Net revenue per plan", "inv.plan", "inv.subtotal - inv.discount + inv.late"),
    ("rev_period", "Net revenue per billing period", "\"p%02d\" % inv.period",
     "inv.subtotal - inv.discount + inv.late"),
    ("tax_region", "Tax charged per region", "inv.region", "inv.tax"),
    ("tax_period", "Tax charged per billing period", "\"p%02d\" % inv.period", "inv.tax"),
    ("disc_region", "Discounts given per region", "inv.region", "inv.discount"),
    ("late_customer", "Late fees per customer", "inv.cust", "inv.late"),
    ("out_customer", "Outstanding amount per customer", "inv.cust", "inv.outstanding()"),
]

SPECIAL = {}
SPECIAL["aging"] = ("Outstanding amount by days overdue", '''"""Report aging: Outstanding amount by days overdue."""
import invoice
import reportutil
import timeutil

NAME = "aging"
TITLE = "Outstanding amount by days overdue"
BUCKETS = (("current", 0), ("1-30", 30), ("31-60", 60), ("61-90", 90), ("91+", None))


def bucket_of(days):
    if days == 0:
        return "current"
    for label, top in BUCKETS[1:]:
        if top is None or days <= top:
            return label
    return BUCKETS[-1][0]


def run(w, cmd):
    cmd.allow("cur", "cust")
    want_cur, want_cust = reportutil.filters(w, cmd)
    rows = {}
    for inv in invoice.live(w):
        if want_cur and inv.currency != want_cur:
            continue
        if want_cust and inv.cust != want_cust:
            continue
        owed = inv.outstanding()
        if owed <= 0:
            continue
        label = bucket_of(timeutil.overdue_days(w.day, inv.due))
        k = (label, inv.currency)
        rows[k] = rows.get(k, 0) + owed
    order = [label for label, _ in BUCKETS]
    reportutil.emit_groups(w, rows, order=order)
''')
SPECIAL["top"] = ("Customers ranked by net revenue in one currency", '''"""Report top: Customers ranked by net revenue in one currency."""
import currencies
import invoice
import money
from errors import CommandError

NAME = "top"
TITLE = "Customers ranked by net revenue in one currency"


def run(w, cmd):
    code = cmd.arg(1)
    if not currencies.known(code):
        raise CommandError("unknown_currency", code)
    limit = money.parse_int(cmd.arg(2, "5"), 1, 100)
    cur = currencies.get(code)
    totals = {}
    for inv in invoice.live(w):
        if inv.currency != code:
            continue
        net = inv.subtotal - inv.discount + inv.late
        totals[inv.cust] = totals.get(inv.cust, 0) + net
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:limit]
    for rank, (cid, net) in enumerate(ranked, 1):
        w.out.emit("  %d %s %s" % (rank, cid, currencies.money_text(cur, net)))
    if not ranked:
        w.out.emit("  (none)")
''')
SPECIAL["usage_units"] = ("Metered units recorded per service", '''"""Report usage_units: Metered units recorded per service."""
import services

NAME = "usage_units"
TITLE = "Metered units recorded per service"


def run(w, cmd):
    totals = {}
    for rec in w.usage:
        totals[rec.svc] = totals.get(rec.svc, 0) + rec.units
    for code in services.codes():
        if code in totals:
            w.out.emit("  %s %d %s" % (code, totals[code], services.get(code).UNIT))
    if not totals:
        w.out.emit("  (none)")
''')
SPECIAL["credits"] = ("Credit held per customer", '''"""Report credits: Credit held per customer."""
import currencies
import customers
import reportutil

NAME = "credits"
TITLE = "Credit held per customer"


def run(w, cmd):
    cmd.allow("cur")
    want_cur, _ = reportutil.filters(w, cmd)
    rows = {}
    for cust in customers.all_sorted(w):
        if want_cur and cust.currency != want_cur:
            continue
        if cust.credit > 0:
            rows[(cust.id, cust.currency)] = cust.credit
    reportutil.emit_groups(w, rows)
''')
SPECIAL["payments"] = ("Payments received per day", '''"""Report payments: Payments received per day."""
import reportutil

NAME = "payments"
TITLE = "Payments received per day"


def run(w, cmd):
    cmd.allow("cur", "cust")
    want_cur, want_cust = reportutil.filters(w, cmd)
    rows = {}
    for e in w.ledger:
        if e.kind != "payment":
            continue
        if want_cust and e.cust != want_cust:
            continue
        if want_cur and w.customers[e.cust].currency != want_cur:
            continue
        k = ("day%04d" % e.day, w.customers[e.cust].currency)
        rows[k] = rows.get(k, 0) + e.amount
    reportutil.emit_groups(w, rows)
''')
SPECIAL["voided"] = ("Invoices that were voided", '''"""Report voided: Invoices that were voided."""
import currencies
import reportutil

NAME = "voided"
TITLE = "Invoices that were voided"


def run(w, cmd):
    cmd.allow("cust")
    _, want_cust = reportutil.filters(w, cmd)
    count = 0
    for inv in w.invoices.values():
        if inv.status != "void":
            continue
        if want_cust and inv.cust != want_cust:
            continue
        cur = currencies.get(inv.currency)
        w.out.emit("  %s %s p%d %s %s" % (inv.number, inv.cust, inv.period, inv.currency,
                                         currencies.money_text(cur, inv.total)))
        count += 1
    w.out.emit("  %d voided" % count)
''')


def gen_reports():
    names = []
    for name, title, key, value in GROUPED:
        source = "invoice.live(w)"
        write("rpt_%s.py" % name, GROUPED_TMPL.format(name=name, title=title, key=key,
                                                      value=value, source=source))
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
    (("customer", "add"), "customers", "cmd_add", "customer add ID PLAN REGION CURRENCY [name=TEXT]"),
    (("customer", "show"), "customers", "cmd_show", "customer show ID"),
    (("customer", "list"), "customers", "cmd_list", "customer list [plan=PLAN] [region=REGION] [status=active|closed]"),
    (("customer", "close"), "closing", "cmd_close", "customer close ID"),
    (("customer", "history"), "customers", "cmd_history", "customer history ID"),
    (("plan", "list"), "plans", "cmd_list", "plan list"),
    (("plan", "show"), "plans", "cmd_show", "plan show PLAN"),
    (("plan", "set"), "planchange", "cmd_set", "plan set ID PLAN"),
    (("service", "list"), "catalog", "cmd_service_list", "service list"),
    (("service", "show"), "catalog", "cmd_service_show", "service show SERVICE"),
    (("region", "list"), "catalog", "cmd_region_list", "region list"),
    (("currency", "list"), "catalog", "cmd_currency_list", "currency list"),
    (("region", "show"), "catalog", "cmd_region_show", "region show REGION"),
    (("quote",), "catalog", "cmd_quote", "quote ID SERVICE UNITS"),
    (("advise",), "catalog", "cmd_advise", "advise ID SERVICE UNITS"),
    (("usage",), "usage", "cmd_usage", "usage ID SERVICE UNITS [day=DAY] [id=TEXT]"),
    (("usage", "batch"), "usagebatch", "cmd_batch",
     "usage batch ID SERVICE UNITS... [day=DAY] [id=PREFIX]"),
    (("usage", "list"), "usage", "cmd_list", "usage list ID [SERVICE]"),
    (("usage", "summary"), "usage", "cmd_summary", "usage summary ID [PERIOD]"),
    (("coupon", "add"), "coupons", "cmd_add", "coupon add ID KIND VALUE [until=DAY] [n=COUNT]"),
    (("coupon", "rm"), "coupons", "cmd_rm", "coupon rm ID NUMBER"),
    (("coupon", "list"), "coupons", "cmd_list", "coupon list ID"),
    (("coupon", "kinds"), "coupons", "cmd_kinds", "coupon kinds"),
    (("invoice", "run"), "invoicing", "cmd_run", "invoice run [PERIOD]"),
    (("invoice", "show"), "invoice", "cmd_show", "invoice show NUMBER"),
    (("invoice", "list"), "invoice", "cmd_list", "invoice list [ID] [state=open|paid|void] [period=N]"),
    (("pay",), "payments", "cmd_pay", "pay ID AMOUNT [inv=NUMBER]"),
    (("credit", "add"), "credits", "cmd_add", "credit add ID AMOUNT"),
    (("refund",), "refunds", "cmd_refund", "refund NUMBER AMOUNT"),
    (("void",), "voids", "cmd_void", "void NUMBER"),
    (("dun",), "dunning", "cmd_dun", "dun"),
    (("statement",), "statements", "cmd_statement", "statement ID [period=N]"),
    (("ledger",), "ledger", "cmd_ledger", "ledger [ID] [kind=KIND]"),
    (("audit",), "audit", "cmd_audit", "audit [COUNT] [action=TEXT] [subject=TEXT]"),
    (("export",), "export", "cmd_export", "export KIND FORMAT"),
    (("report",), "reportcmd", "cmd_report", "report NAME [ARGS]"),
]
for _field, _usage in (("region", "REGION"), ("currency", "CURRENCY"), ("terms", "DAYS"),
                       ("po", "TEXT"), ("exempt", "yes|no"), ("name", "TEXT"),
                       ("email", "ADDRESS"), ("phone", "NUMBER"), ("note", "TEXT")):
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


def main():
    os.makedirs(GOLD, exist_ok=True)
    gen_services()
    gen_taxes()
    gen_discounts()
    gen_currencies()
    gen_setters()
    gen_reports()
    gen_cmdtable()
    print("generated")


if __name__ == "__main__":
    main()
