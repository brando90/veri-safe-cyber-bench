# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Shipment export and import in the tab-separated text form."""
import calib
import ingest
import textnorm
import tsvfmt
import units
from errors import CmdError
from readings import Reading
from shipments import SID_RE, Shipment, apply_fields

BEGIN = "begin export"
END = "end export"


def _opt(value):
    return "-" if value is None else str(value)


def export_ship(world, sid):
    ship = world.ships.get(sid)
    lines = [BEGIN]
    lines.append(tsvfmt.row([
        "ship", ship.sid, tsvfmt.esc(ship.label), ship.route, units.fmt_tenths(ship.lo),
        units.fmt_tenths(ship.hi), _opt(ship.maxexc), _opt(ship.cap), _opt(ship.hmax),
        ship.skew, units.fmt_tenths(ship.offset)]))
    for r in world.store.all(sid):
        lines.append(tsvfmt.row(["r", r.ts, r.temp, _opt(r.hum)]))
    for stop in sorted(ship.arrivals):
        lines.append(tsvfmt.row(["arr", stop, ship.arrivals[stop]]))
    for stop in sorted(ship.plan):
        lines.append(tsvfmt.row(["plan", stop, ship.plan[stop]]))
    lines.append(END)
    return lines


def _ms(text, name):
    if not text.isdigit() or len(text) > 13:
        raise CmdError("bad import block")
    return int(text)


def import_block(world, lines):
    if len(lines) < 3 or lines[0] != BEGIN or lines[-1] != END:
        raise CmdError("bad import block")
    head = tsvfmt.split_row(lines[1])
    if len(head) != 11 or head[0] != "ship":
        raise CmdError("bad import block")
    _tag, sid, label, rid, lo, hi, maxexc, cap, hmax, skew, offset = head
    if not SID_RE.match(sid):
        raise CmdError("bad import block")
    ship = Shipment(sid, textnorm.check_label(label), rid, world.routes.count(rid))
    opts = {"min": lo, "max": hi, "skew": skew, "offset": offset,
            "maxexc": "inherit" if maxexc == "-" else maxexc,
            "cap": "inherit" if cap == "-" else cap,
            "hmax": "inherit" if hmax == "-" else hmax}
    apply_fields(ship, opts)
    rows = []
    for line in lines[2:-1]:
        cells = tsvfmt.split_row(line)
        if cells[0] == "r" and len(cells) == 4:
            hum = None if cells[3] == "-" else units.parse_int(cells[3], "hum", 0, 100)
            temp = units.parse_int(cells[2], "temp", calib.SENSOR_MIN, calib.SENSOR_MAX)
            rows.append(Reading(_ms(cells[1], "t"), temp, hum))
        elif cells[0] == "arr" and len(cells) == 3:
            ship.record_arrival(units.parse_int(cells[1], "stop", 1, 12), _ms(cells[2], "t"))
        elif cells[0] == "plan" and len(cells) == 3:
            ship.plan_stop(units.parse_int(cells[1], "stop", 1, 12), _ms(cells[2], "t"))
        else:
            raise CmdError("bad import block")
    world.store.clear(sid)
    world.ships.replace(ship)
    for r in rows:
        world.store.put(sid, r)
    return len(rows)


HEADER = ("t", "temp", "hum")


def parse_line(line):
    cells = [c.strip() for c in line.split(",")]
    if len(cells) < 2 or len(cells) > 3:
        raise CmdError("bad csv row")
    opts = {"t": cells[0], "temp": cells[1]}
    if len(cells) == 3 and cells[2] != "":
        opts["hum"] = cells[2]
    return opts


def load_csv(world, sid, lines):
    """Feeds each row through the normal read path; returns (accepted, refused, bad)."""
    world.ships.get(sid)
    accepted = refused = bad = 0
    for n, line in enumerate(lines):
        text = line.strip()
        if not text:
            continue
        if n == 0 and text.split(",")[0].strip() == HEADER[0]:
            continue
        try:
            opts = parse_line(text)
            if ingest.accept(world, sid, opts):
                accepted += 1
            else:
                refused += 1
        except CmdError:
            bad += 1
    return accepted, refused, bad
