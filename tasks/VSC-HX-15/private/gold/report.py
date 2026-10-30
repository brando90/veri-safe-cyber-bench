# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Per-shipment summary text."""
import alerts
import excursions
import schedule
import sla
import units


def stops_table(world, ship):
    out = []
    for i, code in enumerate(world.routes.stops(ship.route)):
        when = ship.arrival_at(i + 1)
        state = "pending" if when is None else "arrived %s" % units.fmt_ms(when)
        out.append("  stop %d %s %s" % (i + 1, code, state))
    return out


def summary(world, ship):
    rs = world.store.all(ship.sid)
    found = excursions.find(rs, ship.lo, ship.hi)
    longest = max((e.duration for e in found), default=0)
    out = ['report %s "%s"' % (ship.sid, ship.label)]
    out.extend(stops_table(world, ship))
    out.append("  readings %d" % len(rs))
    out.append("  excursions %d longest %ds" % (len(found), longest))
    out.append("  alerts %d" % len(alerts.for_ship(world, ship)))
    out.append("  handoffs %d" % len(world.custody.chain(ship.sid)))
    late = schedule.late_stops(ship, world.config.get("slack"))
    out.append("  late stops %d" % len(late))
    tenths = sla.percent_tenths(sla.score(world, ship))
    out.append("  sla %s" % ("n/a" if tenths is None else sla.fmt_percent(tenths)))
    return out


def status(ship):
    if not ship.arrivals:
        return "planned"
    if ship.closed() is not None:
        return "delivered"
    return "moving"


def fleet_summary(world):
    counts = {"planned": 0, "moving": 0, "delivered": 0}
    percents = []
    for sid in world.ships.ids():
        ship = world.ships.get(sid)
        counts[status(ship)] += 1
        tenths = sla.percent_tenths(sla.score(world, ship))
        if tenths is not None:
            percents.append(tenths)
    avg = "n/a"
    if percents:
        avg = sla.fmt_percent(units.div_round_half_up(sum(percents), len(percents)))
    return "fleet planned=%d moving=%d delivered=%d avg_sla=%s" % (
        counts["planned"], counts["moving"], counts["delivered"], avg)
