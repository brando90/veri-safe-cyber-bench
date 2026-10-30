# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Orders shipments by how badly they kept their band."""
import alerts
import exposure
import sla
import textnorm
from errors import CmdError

MODES = ("sla", "exposure", "alerts")


def order(world):
    """Returns [(sid, percent tenths or None)], worst first, unscored last."""
    rows = []
    for sid in world.ships.ids():
        sc = sla.score(world, world.ships.get(sid))
        rows.append((sid, sla.percent_tenths(sc), sc))
    scored = [r for r in rows if r[1] is not None]
    scored.sort(key=lambda r: (r[2].inside / r[2].total, textnorm.natural_key(r[0])))
    unscored = [r for r in rows if r[1] is None]
    return [(r[0], r[1]) for r in scored + unscored]


def order_by(world, mode):
    """Returns [(sid, count)] with the largest count first; ties go to the earlier id."""
    if mode not in MODES:
        raise CmdError("rank mode must be one of %s" % ", ".join(MODES))
    rows = []
    for sid in world.ships.ids():
        ship = world.ships.get(sid)
        if mode == "exposure":
            count = exposure.degree_minutes_tenths(world.store.all(sid), ship.lo, ship.hi)
        else:
            count = len(alerts.for_ship(world, ship))
        rows.append((sid, count))
    rows.sort(key=lambda r: (-r[1], textnorm.natural_key(r[0])))
    return rows
