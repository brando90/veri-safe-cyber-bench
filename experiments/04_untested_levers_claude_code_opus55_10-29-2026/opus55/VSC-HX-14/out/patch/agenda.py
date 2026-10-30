# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The agenda: occurrences of all events in a UTC window, in order.

Order: UTC start, then priority (higher first), then event id in natural
order (digit runs compare by value).
"""
import durations
import expand
import names
import timeparse
from errors import CommandError


class Entry:
    __slots__ = ("utc", "ev", "day")

    def __init__(self, ev, day):
        self.ev = ev
        self.day = day
        self.utc = ev.utc(day)


def sort_key(entry):
    return (entry.utc, -entry.ev.prio, names.natural_key(entry.ev.id))


def entries(store, lo_utc_day, hi_utc_day):
    lo = lo_utc_day * 86400
    hi = (hi_utc_day + 1) * 86400
    out = []
    for ev in store.ordered():
        for day in expand.between(ev, lo_utc_day - 1, hi_utc_day + 1):
            e = Entry(ev, day)
            if lo <= e.utc < hi:
                out.append(e)
    out.sort(key=sort_key)
    return out


def firsts(store):
    """One entry per event: its first listed occurrence, in agenda order."""
    out = []
    for ev in store.ordered():
        if ev.id not in store.first_day:
            days = expand.first(ev, 1)
            store.first_day[ev.id] = days[0] if days else None
        if store.first_day[ev.id] is not None:
            out.append(Entry(ev, store.first_day[ev.id]))
    out.sort(key=sort_key)
    return out


def describe(e):
    ev = e.ev
    stamp = timeparse.format_date(e.utc // 86400) if ev.allday else (
        timeparse.format_instant(e.utc) + "Z")
    return "%s %s prio=%d %s %s" % (stamp, ev.id, ev.prio, "\"%s\"" % ev.title,
                                    durations.fmt(ev.dur))


def cmd_agenda(w, cmd):
    lo = timeparse.parse_date(cmd.arg(0))
    hi = timeparse.parse_date(cmd.arg(1))
    if hi < lo:
        raise CommandError("bad_order")
    if hi - lo + 1 > 400:
        raise CommandError("window_too_big", 400)
    limit = parse_limit(cmd.opt("n", "50"))
    rows = entries(w.store, lo, hi)
    for e in rows[:limit]:
        w.emit(describe(e))
    if len(rows) > limit:
        w.emit("... %d more" % (len(rows) - limit))
    if not rows:
        w.emit("no events")


def parse_limit(text):
    if not text.isdecimal() or not 1 <= int(text) <= 1000:
        raise CommandError("bad_number", text)
    return int(text)
