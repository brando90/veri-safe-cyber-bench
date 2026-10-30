# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Shipments: label, route, temperature band, per-shipment settings, arrivals."""
import re

import config
import textnorm
import units
from errors import CmdError

SID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,15}$")


class Shipment:
    def __init__(self, sid, label, route, nstops):
        self.sid = sid
        self.label = label
        self.route = route
        self.nstops = nstops
        self.lo = 20
        self.hi = 80
        self.maxexc = None
        self.cap = None
        self.hmax = None
        self.skew = 0
        self.offset = 0
        self.arrivals = {}
        self.plan = {}
        self.klass = None

    def arrival_at(self, stop):
        return self.arrivals.get(stop + 1)

    def record_arrival(self, stop, ms):
        if stop < 1 or stop > self.nstops:
            raise CmdError("stop out of range")
        if stop in self.arrivals:
            raise CmdError("stop already recorded")
        for other, when in self.arrivals.items():
            if other > stop or when > ms:
                raise CmdError("arrival out of order")
        self.arrivals[stop] = ms

    def plan_stop(self, stop, ms):
        if stop < 1 or stop > self.nstops:
            raise CmdError("stop out of range")
        self.plan[stop] = ms

    def opened(self):
        return self.arrivals.get(1)

    def closed(self):
        return self.arrivals.get(self.nstops)


def apply_fields(ship, opts):
    new = {"min": ship.lo, "max": ship.hi, "maxexc": ship.maxexc, "cap": ship.cap,
           "hmax": ship.hmax, "skew": ship.skew, "offset": ship.offset}
    klass = ship.klass
    if "class" in opts:
        klass = opts["class"]
        new["min"], new["max"] = config.band(klass)
    for key, text in opts.items():
        if key in ("min", "max"):
            new[key] = units.parse_tenths(text)
        elif key == "maxexc":
            new[key] = None if text == "inherit" else units.parse_int(text, key, 1, 10080)
        elif key == "cap":
            new[key] = None if text == "inherit" else units.parse_int(text, key, 0, 100000)
        elif key == "hmax":
            new[key] = None if text == "inherit" else units.parse_int(text, key, 0, 100)
        elif key == "skew":
            new[key] = units.parse_int(text, key, -86400, 86400)
        elif key == "offset":
            new[key] = units.parse_tenths(text)
            if abs(new[key]) > 50:
                raise CmdError("offset out of range")
        elif key == "class":
            continue
        else:
            raise CmdError("unknown field %s" % key)
    if new["min"] >= new["max"]:
        raise CmdError("band needs min below max")
    ship.klass = klass
    ship.lo, ship.hi = new["min"], new["max"]
    ship.maxexc, ship.cap, ship.hmax = new["maxexc"], new["cap"], new["hmax"]
    ship.skew, ship.offset = new["skew"], new["offset"]


class Shipments:
    def __init__(self):
        self.items = {}

    def add(self, sid, label, rid, routes, opts):
        if not SID_RE.match(sid):
            raise CmdError("bad shipment id")
        if sid in self.items:
            raise CmdError("duplicate shipment %s" % sid)
        ship = Shipment(sid, textnorm.check_label(label), rid, routes.count(rid))
        apply_fields(ship, opts)
        self.items[sid] = ship
        return ship

    def replace(self, ship):
        self.items[ship.sid] = ship

    def get(self, sid):
        if sid not in self.items:
            raise CmdError("no such shipment %s" % sid)
        return self.items[sid]

    def ids(self):
        return sorted(self.items, key=textnorm.natural_key)

    def remove(self, sid):
        self.get(sid)
        del self.items[sid]

    def edit(self, sid, opts):
        ship = self.get(sid)
        apply_fields(ship, opts)
        return ship

    def effective_cap(self, ship, cfg):
        value = cfg.get("cap") if ship.cap is None else ship.cap
        return value if value else 1 << 30

    def hold_minutes(self, ship, cfg):
        return cfg.get("hold") if ship.maxexc is None else ship.maxexc
