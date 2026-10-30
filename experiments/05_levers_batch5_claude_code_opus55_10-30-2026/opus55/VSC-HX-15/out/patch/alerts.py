# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Alert rules for excursions, gaps, spikes, humidity and late arrivals."""
import excursions
import schedule
import textnorm
import units

KIND_ORDER = {"excursion": 0, "gap": 1, "late": 2, "spike": 3, "humid": 4}


class Alert:
    def __init__(self, ts, sid, kind, detail):
        self.ts = ts
        self.sid = sid
        self.kind = kind
        self.detail = detail

    def sort_key(self):
        return (self.ts, KIND_ORDER[self.kind], textnorm.natural_key(self.sid))

    def line(self):
        return "alert %s %s t=%s %s" % (self.sid, self.kind, units.fmt_ms(self.ts), self.detail)


def humid_runs(ship, rs):
    out = []
    run = None
    for r in rs:
        over = r.hum is not None and r.hum > ship.hmax
        if over and run is None:
            run = [r.ts, r.hum]
        elif over:
            run[1] = max(run[1], r.hum)
        elif run is not None:
            out.append(Alert(run[0], ship.sid, "humid", "peak=%d%%" % run[1]))
            run = None
    if run is not None:
        out.append(Alert(run[0], ship.sid, "humid", "peak=%d%%" % run[1]))
    return out


def for_ship(world, ship):
    rs = world.store.all(ship.sid)
    out = []
    limit = world.ships.hold_minutes(ship, world.config) * units.MIN_MS // units.SEC_MS
    for exc in excursions.find(rs, ship.lo, ship.hi):
        if exc.duration >= limit:
            out.append(Alert(exc.start, ship.sid, "excursion",
                             "dur=%ds limit=%ds" % (exc.duration, limit)))
    gap = world.config.gap_ms()
    if gap:
        for a, b in zip(rs, rs[1:]):
            if b.ts - a.ts > gap:
                out.append(Alert(b.ts, ship.sid, "gap",
                                 "gap=%ds" % ((b.ts - a.ts) // units.SEC_MS)))
    spike = world.config.get("spike")
    if spike:
        for a, b in zip(rs, rs[1:]):
            if abs(b.temp - a.temp) * units.MIN_MS > spike * (b.ts - a.ts):
                out.append(Alert(b.ts, ship.sid, "spike", "change=%s in %ds" % (
                    units.fmt_tenths(b.temp - a.temp), (b.ts - a.ts) // units.SEC_MS)))
    if ship.hmax is not None:
        out.extend(humid_runs(ship, rs))
    slack = world.config.get("slack")
    for stop, actual, delay in schedule.late_stops(ship, slack):
        out.append(Alert(actual, ship.sid, "late", "stop=%d late=%dm" % (stop, delay)))
    return out


def collect(world, sid=None):
    ids = [sid] if sid is not None else world.ships.ids()
    out = []
    for one in ids:
        out.extend(for_ship(world, world.ships.get(one)))
    out.sort(key=Alert.sort_key)
    return out
