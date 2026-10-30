# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Handlers that only report: rollup, excursions, alerts, sla, rank, find, legs, report and more."""
import unicodedata

import alerts
import cmd_common
import excursions
import exposure
import export
import forecast
import legs
import ranking
import report
import rollup
import schedule
import search
import sla
import textnorm
import units
import windows
from errors import CmdError


def do_rollup(world, pos, opts):
    sid = cmd_common.one_id(pos, "rollup SID")
    world.ships.get(sid)
    rows = rollup.hourly(world.store.all(sid))
    world.emit("rollup %s hours=%d" % (sid, len(rows)))
    for row in rows:
        world.emit(row)


def do_excursions(world, pos, opts):
    sid = cmd_common.one_id(pos, "excursions SID")
    ship = world.ships.get(sid)
    found = excursions.find(world.store.all(sid), ship.lo, ship.hi)
    world.emit("excursions %s n=%d" % (sid, len(found)))
    for e in found:
        text = "  %s start=%s end=%s dur=%ds peak=%s" % (
            e.kind, units.fmt_ms(e.start), units.fmt_ms(e.end), e.duration,
            units.fmt_tenths(e.peak))
        world.emit(text + (" open" if e.is_open else ""))


def do_alerts(world, pos, opts):
    if len(pos) > 1:
        raise CmdError("usage: alerts [SID] [kind=KIND]")
    cmd_common.only(opts, ("kind",), "alerts [SID] [kind=KIND]")
    found = alerts.collect(world, pos[0] if pos else None)
    if "kind" in opts:
        if opts["kind"] not in alerts.KIND_ORDER:
            raise CmdError("unknown alert kind %s" % opts["kind"])
        found = [a for a in found if a.kind == opts["kind"]]
    for a in found:
        world.emit(a.line())
    world.emit("alerts total=%d" % len(found))


def do_sla(world, pos, opts):
    sid = cmd_common.one_id(pos, "sla SID")
    sc = sla.score(world, world.ships.get(sid))
    tenths = sla.percent_tenths(sc)
    if tenths is None:
        world.emit("sla %s n/a" % sid)
    else:
        world.emit("sla %s %s %d/%d" % (sid, sla.fmt_percent(tenths), sc.inside, sc.total))


def do_rank(world, pos, opts):
    if pos:
        raise CmdError("usage: rank [by=sla|exposure|alerts]")
    cmd_common.only(opts, ("by",), "rank [by=sla|exposure|alerts]")
    mode = opts.get("by", "sla")
    if mode != "sla":
        counted = ranking.order_by(world, mode)
        if not counted:
            world.emit("rank empty")
        for place, (sid, count) in enumerate(counted, 1):
            shown = units.fmt_tenths(count) if mode == "exposure" else str(count)
            world.emit("rank %d %s %s" % (place, sid, shown))
        return
    rows = ranking.order(world)
    if not rows:
        world.emit("rank empty")
    for place, (sid, tenths) in enumerate(rows, 1):
        world.emit("rank %d %s %s" % (place, sid, "n/a" if tenths is None else sla.fmt_percent(tenths)))


def do_find(world, pos, opts):
    if not pos or opts:
        raise CmdError("usage: find TEXT")
    query = unicodedata.normalize("NFC", " ".join(pos))
    if not query:
        raise CmdError("empty query")
    hits = search.find(world, query)
    if not hits:
        world.emit("find none")
    for sid in hits:
        world.emit('find %s "%s"' % (sid, world.ships.get(sid).label))


def do_legs(world, pos, opts):
    sid = cmd_common.one_id(pos, "legs SID")
    ship = world.ships.get(sid)
    for line in legs.rows(world, ship):
        world.emit(line)


def do_report(world, pos, opts):
    sid = cmd_common.one_id(pos, "report SID")
    for line in report.summary(world, world.ships.get(sid)):
        world.emit(line)


def do_export(world, pos, opts):
    if opts or len(pos) != 1:
        raise CmdError("usage: export SID | export all")
    ids = world.ships.ids() if pos[0] == "all" else [pos[0]]
    for sid in ids:
        for line in export.export_ship(world, sid):
            world.emit(line)


def do_describe(world, pos, opts):
    usage = "describe SID [from=SECONDS] [to=SECONDS]"
    sid = cmd_common.one_id(pos, usage)
    cmd_common.only(opts, ("from", "to"), usage)
    world.ships.get(sid)
    start, end = cmd_common.user_range(opts)
    text = rollup.describe(windows.select(world.store.all(sid), start, end))
    world.emit("describe %s %s" % (sid, text or "empty"))


def do_plans(world, pos, opts):
    sid = cmd_common.one_id(pos, "plans SID")
    lines = schedule.table(world.ships.get(sid))
    if not lines:
        world.emit("plans %s none" % sid)
    for line in lines:
        world.emit(line)


def do_custody(world, pos, opts):
    sid = cmd_common.one_id(pos, "custody SID")
    world.ships.get(sid)
    chain = world.custody.chain(sid)
    world.emit("custody %s n=%d" % (sid, len(chain)))
    for number, h in enumerate(chain, 1):
        world.emit('  #%d t=%s to="%s" sig=%02d' % (number, units.fmt_ms(h.ts), h.party, h.sig))


def do_fleet(world, pos, opts):
    if pos or opts:
        raise CmdError("usage: fleet")
    world.emit(report.fleet_summary(world))


def do_audit(world, pos, opts):
    if len(pos) > 1 or opts:
        raise CmdError("usage: audit [N]")
    count = units.parse_int(pos[0], "count", 1, 1000) if pos else None
    for line in world.audit.tail(count):
        world.emit(line)


def do_stats(world, pos, opts):
    if pos or opts:
        raise CmdError("usage: stats")
    world.emit("stats ships=%d readings=%d refused=%d sites=%d routes=%d" % (
        len(world.ships.items), world.store.total(), world.quota.refused,
        len(world.sites.names), len(world.routes.items)))


def do_forecast(world, pos, opts):
    usage = "forecast SID [minutes=N]"
    sid = cmd_common.one_id(pos, usage)
    cmd_common.only(opts, ("minutes",), usage)
    ship = world.ships.get(sid)
    minutes = units.parse_int(opts.get("minutes", "30"), "minutes", 1, 1440)
    temp = forecast.project(world.store.all(sid), minutes)
    world.emit("forecast %s +%dm temp=%s %s" % (
        sid, minutes, units.fmt_tenths(temp), forecast.verdict(temp, ship.lo, ship.hi)))


def do_exposure(world, pos, opts):
    sid = cmd_common.one_id(pos, "exposure SID")
    ship = world.ships.get(sid)
    rs = world.store.all(sid)
    total = exposure.degree_minutes_tenths(rs, ship.lo, ship.hi)
    worst = exposure.worst_hour(rs, ship.lo, ship.hi)
    text = "exposure %s %s degmin" % (sid, units.fmt_tenths(total))
    if worst is not None:
        text += " worst_hour=%d (%d readings)" % worst
    world.emit(text)


def do_board(world, pos, opts):
    if pos or opts:
        raise CmdError("usage: board")
    world.emit("board")
    for sid in world.ships.ids():
        ship = world.ships.get(sid)
        sc = sla.score(world, ship)
        tenths = sla.percent_tenths(sc)
        world.emit("  %s %s %s %7s %3d" % (
            sid.ljust(8), textnorm.fit(ship.label, 16), report.status(ship).ljust(9),
            "n/a" if tenths is None else sla.fmt_percent(tenths), len(world.store.all(sid))))


def do_histogram(world, pos, opts):
    usage = "histogram SID [step=TENTHS]"
    sid = cmd_common.one_id(pos, usage)
    cmd_common.only(opts, ("step",), usage)
    world.ships.get(sid)
    step = units.parse_int(opts.get("step", "10"), "step", 1, 1000)
    rows = rollup.histogram(world.store.all(sid), step)
    world.emit("histogram %s step=%s buckets=%d" % (sid, units.fmt_tenths(step), len(rows)))
    for start, count in rows:
        world.emit("  [%s,%s) %d" % (units.fmt_tenths(start), units.fmt_tenths(start + step), count))


def do_compare(world, pos, opts):
    if len(pos) != 2 or opts:
        raise CmdError("usage: compare SID SID")
    world.emit("compare %s %s" % (pos[0], pos[1]))
    scores = []
    for sid in pos:
        ship = world.ships.get(sid)
        rs = world.store.all(sid)
        text = rollup.describe(rs) or "empty"
        tenths = sla.percent_tenths(sla.score(world, ship))
        scores.append(tenths)
        world.emit("  %s %s sla=%s" % (sid, text, "n/a" if tenths is None else sla.fmt_percent(tenths)))
    if None not in scores:
        diff = scores[0] - scores[1]
        world.emit("  sla difference %s%s" % ("-" if diff < 0 else "+", sla.fmt_percent(abs(diff))))
