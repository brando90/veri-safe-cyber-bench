# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Handlers that feed or change data: read, arrive, shift, prune, window, load, import, verify."""
import calib
import cmd_common
import export
import ingest
import retention
import units
import windows
from errors import CmdError


def do_read(world, pos, opts):
    sid = cmd_common.one_id(pos, "read SID t=SECONDS temp=DEGREES [hum=PERCENT]")
    if not ingest.accept(world, sid, opts):
        world.emit("refused %s t=%s cap" % (sid, units.fmt_ms(units.parse_ms(opts["t"]))))


def do_arrive(world, pos, opts):
    usage = "arrive SID stop=N t=SECONDS"
    sid = cmd_common.one_id(pos, usage)
    cmd_common.only(opts, ("stop", "t"), usage)
    ship = world.ships.get(sid)
    stop = units.parse_int(cmd_common.need(opts, "stop"), "stop", 1, 12)
    ms = units.parse_ms(cmd_common.need(opts, "t"))
    ship.record_arrival(stop, ms)
    world.emit("ok arrive %s stop %d %s" % (sid, stop, world.routes.stop_at(ship.route, stop - 1)))


def do_shift(world, pos, opts):
    usage = "shift SID seconds=N"
    sid = cmd_common.one_id(pos, usage)
    cmd_common.only(opts, ("seconds",), usage)
    world.ships.get(sid)
    delta = units.parse_int(cmd_common.need(opts, "seconds"), "seconds", -86400 * 30, 86400 * 30)
    moved = [r._replace(ts=calib.correct(r.ts, delta * units.SEC_MS))
             for r in world.store.all(sid)]
    world.store.replace_all(sid, moved)
    world.emit("ok shift %s n=%d" % (sid, len(moved)))


def do_prune(world, pos, opts):
    usage = "prune now=SECONDS [dry=yes]"
    if pos:
        raise CmdError("usage: " + usage)
    cmd_common.only(opts, ("now", "dry"), usage)
    now = units.parse_ms(cmd_common.need(opts, "now"))
    if opts.get("dry", "no") not in ("yes", "no"):
        raise CmdError("dry must be yes or no")
    dry = opts.get("dry") == "yes"
    removed = retention.prune(world, now, dry)
    world.emit("%s prune %s=%d" % ("ok" if not dry else "dry", "removed" if not dry else "would_remove", removed))


def reading_line(r):
    text = "  %s %s" % (units.fmt_ms(r.ts), units.fmt_tenths(r.temp))
    if r.hum is not None:
        text += " hum=%d" % r.hum
    return text


def do_window(world, pos, opts):
    usage = "window SID [from=SECONDS] [to=SECONDS]"
    sid = cmd_common.one_id(pos, usage)
    cmd_common.only(opts, ("from", "to"), usage)
    world.ships.get(sid)
    start, end = cmd_common.user_range(opts)
    part = windows.select(world.store.all(sid), start, end)
    world.emit("window %s n=%d" % (sid, len(part)))
    for r in part:
        world.emit(reading_line(r))


def do_timeline(world, pos, opts):
    usage = "timeline SID [from=SECONDS] [to=SECONDS]"
    sid = cmd_common.one_id(pos, usage)
    cmd_common.only(opts, ("from", "to"), usage)
    world.ships.get(sid)
    start, end = cmd_common.user_range(opts)
    part = windows.select(world.store.all(sid), start, end)
    world.emit("timeline %s n=%d" % (sid, len(part)))
    for r in part:
        text = "  %s %s" % (units.day_clock(r.ts), units.fmt_tenths(r.temp))
        if r.hum is not None:
            text += " hum=%d" % r.hum
        world.emit(text)


def do_load(world, pos, lines):
    sid = cmd_common.one_id(pos, "load SID")
    accepted, refused, bad = export.load_csv(world, sid, lines)
    world.emit("ok load %s accepted=%d refused=%d bad=%d" % (sid, accepted, refused, bad))


def do_import(world, lines):
    count = export.import_block(world, lines)
    world.emit("ok import readings=%d" % count)


def do_verify(world, pos, opts):
    usage = "verify SID N sig=NN"
    if len(pos) != 2:
        raise CmdError("usage: " + usage)
    cmd_common.only(opts, ("sig",), usage)
    world.ships.get(pos[0])
    number = units.parse_int(pos[1], "number", 1, 100000)
    sig = units.parse_int(cmd_common.need(opts, "sig"), "sig", 0, 99)
    ok = world.custody.verify(pos[0], number, sig)
    world.emit("verify %s #%d %s" % (pos[0], number, "ok" if ok else "mismatch"))
