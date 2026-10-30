# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""In-band share of a shipment's readings."""
import units
import windows


class Score:
    def __init__(self, inside, total):
        self.inside = inside
        self.total = total


def score(world, ship):
    rs = world.store.all(ship.sid)
    opened, closed = ship.opened(), ship.closed()
    if opened is not None and closed is not None:
        rs = windows.select(rs, opened, closed)
    inside = sum(1 for r in rs if ship.lo <= r.temp <= ship.hi)
    return Score(inside, len(rs))


def percent_tenths(sc):
    if sc.total == 0:
        return None
    return units.div_round_half_up(sc.inside * 1000, sc.total)


def fmt_percent(tenths):
    return "%d.%d%%" % (tenths // 10, tenths % 10)
