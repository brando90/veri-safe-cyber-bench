# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Report scrap_cat: Units scrapped, expired or written off per category."""
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
