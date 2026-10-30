# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Report expiring: Lots that expire within N days (default 7)."""
import money
import reportutil

NAME = "expiring"
TITLE = "Lots that expire within N days (default 7)"


def run(w, cmd):
    cmd.allow("wh", "days")
    want_wh, _ = reportutil.filters(w, cmd)
    days = money.parse_int(cmd.opt("days", "7"), 0, 400)
    count = 0
    for lot in sorted(w.lots.values(), key=lambda x: (x.expiry is None, x.expiry, x.id)):
        if lot.expiry is None:
            continue
        if want_wh and lot.wh != want_wh:
            continue
        left = lot.expiry - w.day
        if 0 <= left <= days:
            w.out.emit("  %s %s %s qty=%d expiry=%d days_left=%d" % (
                lot.id, lot.wh, lot.sku, lot.qty, lot.expiry, left))
            count += 1
    if not count:
        w.out.emit("  (none)")
