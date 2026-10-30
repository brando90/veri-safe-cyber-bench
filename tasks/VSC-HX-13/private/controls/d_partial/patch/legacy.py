# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Version 1 flat-rate rating, kept for the old import files.  Nothing in
the current command set calls it."""
import money

FLAT_RATES = {"storage": 3, "egress": 5, "compute": 11, "requests": 2}
FREE_UNITS = 1000


def flat_charge(service, units):
    rate = FLAT_RATES.get(service)
    if rate is None:
        return 0
    billable = max(0, units - FREE_UNITS)
    return money.ceil_div(billable * rate, 100)


def flat_total(records):
    total = 0
    for service, units in records:
        total += flat_charge(service, units)
    return total


def parse_import_line(text):
    parts = text.split(",")
    if len(parts) != 3:
        return None
    cust, service, units = parts
    if not units.isdigit():
        return None
    return cust.strip(), service.strip(), int(units)


def import_lines(lines):
    records = []
    for text in lines:
        rec = parse_import_line(text)
        if rec is not None:
            records.append(rec)
    return records


def old_proration(fee, days):
    return fee * days // 30


def old_late_fee(amount, days_late):
    if days_late <= 0:
        return 0
    return max(100, amount * 2 // 100) + 25 * (days_late // 30)


def old_tax(amount, rate_percent):
    return amount * rate_percent // 100


def old_invoice_total(records, rate_percent):
    net = flat_total(records)
    return net + old_tax(net, rate_percent)


def render_old_invoice(cust, records, rate_percent):
    rows = ["INVOICE %s" % cust]
    for service, units in records:
        rows.append("%-10s %8d %8d" % (service, units, flat_charge(service, units)))
    rows.append("TOTAL %d" % old_invoice_total(records, rate_percent))
    return rows
