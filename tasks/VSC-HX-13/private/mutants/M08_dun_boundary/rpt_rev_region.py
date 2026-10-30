# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Report rev_region: Net revenue per tax region."""
import invoice
import reportutil

NAME = "rev_region"
TITLE = "Net revenue per tax region"


def key_of(inv):
    return inv.region


def value_of(inv):
    return inv.subtotal - inv.discount + inv.late


def run(w, cmd):
    cmd.allow("cur", "cust")
    want_cur, want_cust = reportutil.filters(w, cmd)
    rows = {}
    for inv in invoice.live(w):
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
