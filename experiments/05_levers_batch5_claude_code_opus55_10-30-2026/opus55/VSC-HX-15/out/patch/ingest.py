# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Turns a read command into a stored reading."""
import calib
import units
from errors import CmdError
from readings import Reading

KNOWN = ("t", "temp", "hum")


def accept(world, sid, opts):
    """Stores one reading; returns False when the intake cap refused it."""
    ship = world.ships.get(sid)
    for key in opts:
        if key not in KNOWN:
            raise CmdError("unknown field %s" % key)
    if "t" not in opts or "temp" not in opts:
        raise CmdError("read needs t= and temp=")
    # skew > 0: the logger clock runs ahead, so the reference instant is earlier.
    ts = calib.correct(units.parse_ms(opts["t"]), -ship.skew * units.SEC_MS)
    # calibration first, clamp last (calib.calibrate clamps)
    raw = units.parse_tenths(opts["temp"])
    temp = calib.calibrate(raw, ship.offset)
    hum = None
    if "hum" in opts:
        hum = units.parse_int(opts["hum"], "hum", 0, 100)
    reading = Reading(ts, temp, hum)
    if world.store.has(sid, ts):
        world.store.put(sid, reading)
        return True
    limit = world.ships.effective_cap(ship, world.config)
    if not world.quota.admit(sid, ts, limit):
        return False
    world.store.put(sid, reading)
    return True
