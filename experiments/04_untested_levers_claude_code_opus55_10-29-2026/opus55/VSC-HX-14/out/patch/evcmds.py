# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Event commands: add, show, change, remove, skip and expand."""
import civil
import durations
import events
import expand
import fields
import ids
import offsets
import rules
import timeparse
from errors import CommandError
from events import Event
from output import kv, quote

MAX_WINDOW = 3660


def parse_flag(cmd, name):
    value = cmd.opt(name, "no")
    if value not in ("yes", "no"):
        raise CommandError("bad_flag", value, name)
    return value == "yes"


def parse_prio(text):
    if not text.isdecimal() or int(text) > 9:
        raise CommandError("bad_prio", text)
    return int(text)


def cmd_add(w, cmd):
    requested = cmd.arg(0)
    requested = None if requested == "-" else requested
    title = fields.clean_title(cmd.arg(1))
    allday = parse_flag(cmd, "allday")
    start, raw = timeparse.parse_start(cmd.arg(2), allday)
    dur = durations.parse(cmd.opt("dur", "1d" if allday else "1h"))
    rule = rules.parse(cmd.opt("rule")) if cmd.opt("rule") is not None else None
    tz = offsets.parse(cmd.opt("tz", "Z"))
    prio = parse_prio(cmd.opt("prio", "5"))
    cats = fields.clean_cats(cmd.opt("cat", ""))
    eid, seq = w.store.allocate(requested)
    ev = Event(eid, seq, title, start, raw, dur, rule, tz, allday, prio, cats, [])
    w.store.insert(ev)
    w.emit("added %s ref=%s" % (ev.id, ids.encode(ev.seq)))


def cmd_show(w, cmd):
    ev = w.store.find(cmd.arg(0))
    w.emit("event %s ref=%s" % (ev.id, ids.encode(ev.seq)))
    w.emit("  title %s" % quote(ev.title))
    when = timeparse.format_date(ev.start // 86400) if ev.allday else (
        timeparse.format_instant(ev.start))
    w.emit("  start %s%s" % (when, " (given %s)" % timeparse.format_exact(ev.raw)
                             if ev.raw != ev.start else ""))
    w.emit("  dur %s tz %s prio %d%s" % (durations.fmt(ev.dur), offsets.fmt(ev.tz), ev.prio,
                                         " allday" if ev.allday else ""))
    w.emit("  rule %s" % (ev.rule.text() if ev.rule else "-"))
    w.emit("  cats %s" % (fields.join_list(ev.cats) if ev.cats else "-"))
    if ev.skips:
        w.emit("  skips %s" % ",".join(timeparse.format_date(d) for d in ev.skips))


def cmd_rm(w, cmd):
    ev = w.store.find(cmd.arg(0))
    w.store.remove(ev)
    w.emit("removed %s" % ev.id)


def cmd_move(w, cmd):
    ev = w.store.find(cmd.arg(0))
    start, raw = timeparse.parse_start(cmd.arg(1), ev.allday)
    events.reschedule(ev, start, raw, ev.rule)
    w.store.touch(ev)
    w.emit("moved %s to %s" % (ev.id, timeparse.format_instant(ev.start)))


def cmd_rule(w, cmd):
    ev = w.store.find(cmd.arg(0))
    text = cmd.arg(1)
    rule = None if text == "none" else rules.parse(text)
    events.reschedule(ev, ev.start, ev.raw, rule)
    w.store.touch(ev)
    w.emit("rule of %s is %s" % (ev.id, rule.text() if rule else "-"))


def cmd_retitle(w, cmd):
    ev = w.store.find(cmd.arg(0))
    ev.title = fields.clean_title(cmd.arg(1))
    w.store.touch(ev)
    w.emit("title of %s is %s" % (ev.id, quote(ev.title)))


def cmd_cat(w, cmd):
    ev = w.store.find(cmd.arg(0))
    ev.cats = fields.clean_cats(cmd.arg(1) if cmd.arg(1) != "-" else "")
    w.store.touch(ev)
    w.emit("cats of %s are %s" % (ev.id, fields.join_list(ev.cats) if ev.cats else "-"))


def cmd_set(w, cmd):
    ev = w.store.find(cmd.arg(0))
    dur = durations.parse(cmd.opt("dur")) if cmd.opt("dur") is not None else ev.dur
    tz = offsets.parse(cmd.opt("tz")) if cmd.opt("tz") is not None else ev.tz
    prio = parse_prio(cmd.opt("prio")) if cmd.opt("prio") is not None else ev.prio
    ev.dur, ev.tz, ev.prio = dur, tz, prio
    w.store.touch(ev)
    w.emit("updated %s: %s %s prio=%d" % (ev.id, durations.fmt(dur), offsets.fmt(tz), prio))


def cmd_skip(w, cmd):
    ev = w.store.find(cmd.arg(0))
    if ev.rule is None:
        raise CommandError("not_recurring", ev.id)
    text = cmd.arg(1)
    day = timeparse.parse_date(text)
    if day not in expand.between(ev, day, day, with_skips=True):
        raise CommandError("not_occurrence", text, ev.id)
    if day in ev.skips:
        raise CommandError("already_skipped", text, ev.id)
    ev.skips = sorted(ev.skips + [day])
    w.store.touch(ev)
    w.emit("skipped %s on %s" % (ev.id, text))


def cmd_unskip(w, cmd):
    ev = w.store.find(cmd.arg(0))
    text = cmd.arg(1)
    day = timeparse.parse_date(text)
    if day not in ev.skips:
        raise CommandError("not_skipped", text, ev.id)
    ev.skips.remove(day)
    w.store.touch(ev)
    w.emit("restored %s on %s" % (ev.id, text))


def cmd_expand(w, cmd):
    ev = w.store.find(cmd.arg(0))
    lo = timeparse.parse_date(cmd.arg(1))
    hi = timeparse.parse_date(cmd.arg(2))
    if hi < lo:
        raise CommandError("bad_order")
    if hi - lo + 1 > MAX_WINDOW:
        raise CommandError("window_too_big", MAX_WINDOW)
    days = expand.between(ev, lo, hi)
    clock = "all-day" if ev.allday else timeparse.format_clock(ev.start % 86400)
    for d in days:
        w.emit("%s %s %s" % (timeparse.format_date(d), civil.weekday_name(d), clock))
    w.emit("%d occurrences" % len(days))


def cmd_list(w, cmd):
    rows = w.store.ordered()
    for ev in rows:
        when = timeparse.format_date(ev.start // 86400) if ev.allday else (
            timeparse.format_instant(ev.start))
        w.emit("%s %s %s %s%s" % (ids.encode(ev.seq), ev.id, when, quote(ev.title),
                                  " " + kv("rule", ev.rule.text()) if ev.rule else ""))
    w.emit("%d events" % len(rows))
