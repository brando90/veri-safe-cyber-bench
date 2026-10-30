# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Register of the deliberate exceptions (decoys) of gold.

Each decoy has an id, the module it lives in, whether it is among the more
suspicious-looking ones (it deviates visibly from its siblings in code), the
README special case or table that documents it, and a 'tidy' edit: the
change a defect-hungry fixer would make to bring it in line with its
siblings.  check_decoys.py applies every tidy edit to gold on its own and
requires at least one ref_tests case to fail."""

# (id, file, suspicious, documented in, [(old, new), ...])
DECOYS = [
    # ---- warehouses
    ("W01_iris_cutoff24", "wh_iris.py", False, "special case 5", [("CUTOFF = 24\n", "CUTOFF = 16\n")]),
    ("W02_kelp_cutoff0", "wh_kelp.py", False, "special case 5", [("CUTOFF = 0\n", "CUTOFF = 16\n")]),
    ("W03_harbor_seven_days", "wh_harbor.py", False, "table",
     [("OPEN_DAYS = (0, 1, 2, 3, 4, 5, 6)\n", "OPEN_DAYS = (0, 1, 2, 3, 4)\n")]),
    ("W04_cedar_soft_capacity", "wh_cedar.py", True, "special case 1",
     [("    return CAPACITY + CAPACITY // 10\n", "    return CAPACITY\n")]),
    ("W05_juniper_per_unit", "wh_juniper.py", True, "special case 2",
     [("    return PICK_FEE * units + PACK_FEE\n", "    return PICK_FEE * lines + PACK_FEE\n")]),
    ("W06_elm_saturday", "wh_elm.py", True, "special case 3",
     [("    if timeutil.weekday(day) == 5:\n        return SATURDAY_CUTOFF\n    return CUTOFF\n",
       "    return CUTOFF\n")]),
    ("W07_larch_preferred", "wh_larch.py", False, "special case 4",
     [("    if region_code in PREFERRED:\n        return 0\n", "")]),
    ("W08_fjord_closed_monday", "wh_fjord.py", False, "table",
     [("OPEN_DAYS = (1, 2, 3, 4, 5)\n", "OPEN_DAYS = (0, 1, 2, 3, 4)\n")]),
    # ---- categories
    ("C01_cables_loose", "cat_cables.py", False, "special case 6",
     [('    """Units booked for a receipt of UNITS."""\n    return units\n',
       '    """Units booked for a receipt of UNITS."""\n    return money.ceil_div(units, PACK) * PACK\n')]),
    ("C02_lumber_kilograms", "cat_lumber.py", True, "special case 9",
     [("    return money.ceil_div(qty * UNIT_G, 1000) * 1000\n", "    return qty * UNIT_G\n")]),
    ("C03_medicine_given_expiry", "cat_medicine.py", True, "special case 10",
     [('    if given is None:\n        raise CommandError("need_expiry", CODE)\n'
       '    return money.parse_int(given, day, day + 3650)\n',
       '    if given is not None:\n        raise CommandError("bad_option", "exp")\n'
       '    if SHELF == 0:\n        return None\n    return day + SHELF\n')]),
    ("C04_dairy_no_returns", "cat_dairy.py", False, "special case 12",
     [("RETURN_WINDOW = 0\n", "RETURN_WINDOW = 7\n")]),
    ("C05_produce_never_restocks", "cat_produce.py", False, "special case 12",
     [('RESTOCK = "never"\n', 'RESTOCK = "always"\n')]),
    ("C06_glassware_padding", "cat_glassware.py", True, "special case 8",
     [("    return qty * UNIT_G + money.pct(qty * UNIT_G, PADDING_BP)\n", "    return qty * UNIT_G\n")]),
    ("C07_fasteners_whole_packs", "cat_fasteners.py", True, "special case 7",
     [('    if qty % PACK:\n        raise CommandError("pack_multiple", CODE, PACK, qty)\n', "")]),
    ("C08_paper_made_to_order", "cat_paper.py", True, "special case 11",
     [("def needs_reorder(available):\n    return False\n",
       "def needs_reorder(available):\n    return REORDER > 0 and available <= REORDER\n")]),
    ("C09_tools_no_line_limit", "cat_tools.py", False, "special case 12",
     [("MAX_LINE = 0\n", "MAX_LINE = 500\n")]),
    ("C10_solvents_never_restock", "cat_solvents.py", False, "special case 12",
     [('RESTOCK = "never"\n', 'RESTOCK = "always"\n')]),
    ("C11_frozen_margin", "cat_frozen.py", False, "table", [("MARGIN = 10\n", "MARGIN = 0\n")]),
    ("C12_snacks_never_restock", "cat_snacks.py", False, "special case 12",
     [('RESTOCK = "never"\n', 'RESTOCK = "always"\n')]),
    ("C13_medicine_margin", "cat_medicine.py", False, "table", [("MARGIN = 30\n", "MARGIN = 0\n")]),
    # ---- carriers
    ("K01_parcelo_flat", "car_parcelo.py", False, "special case 13", [("STEP_COST = 0\n", "STEP_COST = 40\n")]),
    ("K02_haul_no_parcel_limit", "car_haul.py", False, "special case 13", [("MAX_G = 0\n", "MAX_G = 20000\n")]),
    ("K03_aero_fixed_transit", "car_aero.py", True, "special case 14",
     [("    return TRANSIT_BASE\n", "    return TRANSIT_BASE + distance // TRANSIT_STEP\n")]),
    ("K04_nord_truncated_fuel", "car_nord.py", True, "special case 15",
     [("    fuel = (sub + zone) * FUEL_BP // 10000\n", "    fuel = money.pct(sub + zone, FUEL_BP)\n")]),
    ("K05_gull_base_only", "car_gull.py", True, "special case 16",
     [("    basis = parcels(weight) * BASE\n    sub = rate(weight)\n    zone = money.pct(basis, distance * ZONE_BP)\n"
       "    fuel = money.pct(basis + zone, FUEL_BP)\n",
       "    sub = rate(weight)\n    zone = money.pct(sub, distance * ZONE_BP)\n"
       "    fuel = money.pct(sub + zone, FUEL_BP)\n")]),
    ("K06_tern_regions", "car_tern.py", False, "special case 13 and table",
     [("COVERS = ('arden', 'brook', 'crest', 'delta', 'ember', 'forge')\n", "COVERS = None\n")]),
    ("K07_pony_total_limit", "car_pony.py", False, "special case 13", [("MAX_TOTAL = 5000\n", "MAX_TOTAL = 0\n")]),
    ("K08_zed_minimum_first", "car_zed.py", True, "special case 17",
     [("    sub = max(rate(weight), MIN_CHARGE)\n    zone = money.pct(sub, distance * ZONE_BP)\n"
       "    fuel = money.pct(sub + zone, FUEL_BP)\n    return sub + zone + fuel\n",
       "    sub = rate(weight)\n    zone = money.pct(sub, distance * ZONE_BP)\n"
       "    fuel = money.pct(sub + zone, FUEL_BP)\n    return max(sub + zone + fuel, MIN_CHARGE)\n")]),
    # ---- regions
    ("R01_depot_pickup", "shipping.py", True, "special case 22",
     [("    if region.ZONE == 0:\n", "    if region.ZONE < 0:\n")]),
    ("R02_delta_split_duty", "reg_delta.py", True, "special case 18",
     [("    return money.pct(value, PARTS[0]) + money.pct(value, PARTS[1])\n",
       "    return money.pct(value, DUTY_BP)\n")]),
    ("R03_ember_duty_up", "reg_ember.py", True, "special case 19",
     [("    return money.ceil_div(value * DUTY_BP, 10000)\n", "    return money.pct(value, DUTY_BP)\n")]),
    ("R04_forge_weekend", "reg_forge.py", False, "table", [("WEEKEND = (4, 5)\n", "WEEKEND = (5, 6)\n")]),
    ("R05_gale_no_duty", "reg_gale.py", False, "special case 21", [("DUTY_BP = 0\n", "DUTY_BP = 800\n")]),
    ("R06_haven_all_dutiable", "reg_haven.py", False, "special case 21", [("DUTY_FREE = 0\n", "DUTY_FREE = 8000\n")]),
    ("R07_crest_ban_level", "reg_crest.py", False, "table", [("BAN_HAZ = 2\n", "BAN_HAZ = 4\n")]),
    # ---- accounts and commands
    ("X01_note_on_closed", "set_note.py", True, "special case 23",
     [("customers.get(w, cmd.arg(0))", "customers.open(w, cmd.arg(0))")]),
    ("X02_note_not_audited", "set_note.py", True, "special case 23",
     [("    cust.note = value\n", '    cust.note = value\n    w.audit_add("set note", cust.id, show(old), show(value))\n')]),
    ("X03_region_open_orders", "set_region.py", False, "special case 23",
     [('    if customers.open_orders(w, cust.id):\n        raise CommandError("open_orders", cust.id)\n', "")]),
    ("X04_carrier_serves_region", "set_carrier.py", False, "special case 23",
     [('        if not car.covers(cust.region):\n            raise CommandError("carrier_region", text, cust.region)\n', "")]),
    ("X05_cancelled_report_all", "rpt_cancelled.py", True, "special case 27",
     [("    for order in w.orders.values():\n", "    for order in orders.live(w):\n")]),
    ("X06_return_closed_ok", "returns.py", True, "special case 24",
     [("    customers.get(w, order.cust)\n", "    customers.open(w, order.cust)\n")]),
    ("X07_ship_closed_ok", "shipping.py", True, "special case 24",
     [("    cust = customers.get(w, order.cust)\n    hour", "    cust = customers.open(w, order.cust)\n    hour")]),
    ("X08_cancel_closed_ok", "orders.py", False, "special case 24",
     [("    order = find(w, cmd.arg(0))\n    if sum(line.pending() for line in order.lines) == 0:\n",
       "    order = find(w, cmd.arg(0))\n    customers.open(w, order.cust)\n    if sum(line.pending() for line in order.lines) == 0:\n")]),
    ("X09_backorder_closed_ok", "backorders.py", False, "special case 24",
     [("        if cust.hold:\n            continue\n", "        if cust.hold or cust.status == \"closed\":\n            continue\n")]),
    ("X10_transfer_capacity_exempt", "transfers.py", True, "special case 25",
     [("    movable = [lot for lot in",
       "    if not dst.accepts_units(stock.total_units(w, dst.CODE), units):\n"
       "        raise CommandError(\"over_capacity\", dst.CODE, stock.total_units(w, dst.CODE), dst.limit())\n"
       "    movable = [lot for lot in")]),
    ("X11_backorder_skips_hold", "backorders.py", False, "special case 24",
     [("        if cust.hold:\n            continue\n", "")]),
    ("X12_ship_ignores_hold", "shipping.py", False, "special case 24",
     [("    hour = money.parse_int(", "    if cust.hold:\n        raise CommandError(\"on_hold\", cust.id)\n    hour = money.parse_int(")]),
    ("X13_free_freight_only_freight", "shipping.py", True, "special case 26",
     [("    handling = wh.handling(len(qty), sum(qty.values()))\n",
       "    handling = 0 if tiers.free_freight(cust.tier, order.goods) else wh.handling(len(qty), sum(qty.values()))\n")]),
    ("X14_duplicate_lines_added", "orders.py", False, "orders section",
     [("        merged[sku] = merged.get(sku, 0) + int(m.group(2))\n",
       "        if sku in merged:\n            raise CommandError(\"bad_line\", text)\n        merged[sku] = int(m.group(2))\n")]),
    ("X15_report_cust_closed_ok", "reportutil.py", False, "special case 27",
     [("        customers.get(w, want_cust)\n", "        customers.open(w, want_cust)\n")]),
]

# the six most suspicious-looking deviations: the 'tidy-up fix' control
TIDY_SIX = ["X01_note_on_closed", "X05_cancelled_report_all", "K04_nord_truncated_fuel",
            "R03_ember_duty_up", "W04_cedar_soft_capacity", "X10_transfer_capacity_exempt"]
# a second group of tidy-ups (cross-checks)
TIDY_MORE = ["K05_gull_base_only", "K08_zed_minimum_first", "X06_return_closed_ok",
             "X07_ship_closed_ok", "C07_fasteners_whole_packs", "W05_juniper_per_unit",
             "X13_free_freight_only_freight", "R01_depot_pickup"]
