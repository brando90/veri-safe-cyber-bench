# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Report usage_units: Metered units recorded per service."""
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
