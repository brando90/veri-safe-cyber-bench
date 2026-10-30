# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Report stock_cat: Units on hand per category."""
import reportutil
import skus
import stock

NAME = "stock_cat"
TITLE = "Units on hand per category"
KIND = "units"


def key_of(lot):
    return skus.category(lot.sku)


def value_of(lot):
    return lot.qty


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
