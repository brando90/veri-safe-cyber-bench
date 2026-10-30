# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Handlers for the setup commands: set, config, site, route, ship, plan, handoff."""
import cmd_common
import config
import report
import textnorm
import units
from errors import CmdError


def do_set(world, pos, opts):
    if len(pos) != 2 or opts:
        raise CmdError("usage: set KEY VALUE")
    value = world.config.set(pos[0], pos[1])
    world.emit("ok set %s=%d" % (pos[0], value))


def do_config(world, pos, opts):
    if pos or opts:
        raise CmdError("usage: config")
    world.emit(world.config.line())


def do_site(world, pos, opts):
    if not pos:
        raise CmdError("usage: site add CODE NAME | site list | site export")
    if pos[0] == "export" and len(pos) == 1 and not opts:
        for line in world.sites.export_lines():
            world.emit(line)
        return
    if pos[0] == "list" and len(pos) == 1 and not opts:
        for code in sorted(world.sites.names):
            world.emit('site %s "%s"' % (code, world.sites.name(code)))
        return
    if pos[0] != "add" or len(pos) < 3 or opts:
        raise CmdError("usage: site add CODE NAME | site list | site export")
    code = world.sites.add(pos[1], " ".join(pos[2:]))
    world.emit("ok site %s" % code)


def do_route(world, pos, opts):
    if len(pos) < 4 or pos[0] != "add" or opts:
        raise CmdError("usage: route add ID CODE CODE...")
    world.routes.add(pos[1], pos[2:], world.sites)
    world.emit("ok route %s stops=%d" % (pos[1], world.routes.count(pos[1])))


def describe_ship(world, ship):
    hold = world.ships.hold_minutes(ship, world.config)
    cap = world.ships.effective_cap(ship, world.config)
    hmax = "-" if ship.hmax is None else "%d%%" % ship.hmax
    return 'ship %s "%s" route=%s class=%s band=%s..%s hold=%dm cap=%s hmax=%s skew=%ds offset=%s' % (
        ship.sid, ship.label, ship.route, ship.klass or "-", units.fmt_tenths(ship.lo),
        units.fmt_tenths(ship.hi), hold, "unlimited" if cap == 0 else cap, hmax, ship.skew,
        units.fmt_tenths(ship.offset))


def do_ship(world, pos, opts):
    usage = "usage: ship add ID LABEL route=R [options] | ship edit ID options | ship show ID | ship list | ship rename ID LABEL | ship remove ID"
    if not pos:
        raise CmdError(usage)
    verb = pos[0]
    if verb == "add" and len(pos) >= 3:
        opts = dict(opts)
        if "route" not in opts:
            raise CmdError("missing route=")
        rid = opts.pop("route")
        world.ships.add(pos[1], " ".join(pos[2:]), rid, world.routes, opts)
        world.emit("ok ship %s" % pos[1])
    elif verb == "edit" and len(pos) == 2:
        world.ships.edit(pos[1], opts)
        world.emit("ok ship %s" % pos[1])
    elif verb == "show" and len(pos) == 2 and not opts:
        world.emit(describe_ship(world, world.ships.get(pos[1])))
    elif verb == "list" and len(pos) == 1 and not opts:
        for sid in world.ships.ids():
            ship = world.ships.get(sid)
            world.emit("ship %s %s readings=%d" % (
                sid, report.status(ship), len(world.store.all(sid))))
    elif verb == "rename" and len(pos) >= 3 and not opts:
        ship = world.ships.get(pos[1])
        ship.label = textnorm.check_label(" ".join(pos[2:]))
        world.emit("ok ship %s" % pos[1])
    elif verb == "remove" and len(pos) == 2 and not opts:
        world.ships.remove(pos[1])
        world.store.clear(pos[1])
        world.custody.drop(pos[1])
        world.emit("ok remove %s" % pos[1])
    else:
        raise CmdError(usage)


def do_profiles(world, pos, opts):
    if pos or opts:
        raise CmdError("usage: profiles")
    for line in config.listing():
        world.emit(line)


def do_plan(world, pos, opts):
    usage = "plan SID stop=N t=SECONDS"
    sid = cmd_common.one_id(pos, usage)
    cmd_common.only(opts, ("stop", "t"), usage)
    ship = world.ships.get(sid)
    stop = units.parse_int(cmd_common.need(opts, "stop"), "stop", 1, 12)
    ship.plan_stop(stop, units.parse_ms(cmd_common.need(opts, "t")))
    world.emit("ok plan %s stop %d" % (sid, stop))


def do_handoff(world, pos, opts):
    usage = "handoff SID PARTY t=SECONDS"
    if len(pos) < 2:
        raise CmdError("usage: " + usage)
    cmd_common.only(opts, ("t",), usage)
    world.ships.get(pos[0])
    ts = units.parse_ms(cmd_common.need(opts, "t"))
    number = world.custody.add(pos[0], ts, " ".join(pos[1:]))
    world.emit("ok handoff %s #%d sig=%02d" % (pos[0], number, world.custody.chain(pos[0])[-1].sig))
