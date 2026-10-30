# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The program's own consistency check.

``full_check`` runs after every command (on the events the command
touched, plus the store-wide rules) and on ``check`` (on every event).  A
failure raises InvariantViolation; main prints ``INVARIANT: ...`` on
standard error and exits 86.
"""
import re

import agenda
import civil
import expand
import fields
import ids
import offsets
import pack
import rules
import textrec
from errors import CommandError, InvariantViolation

SERIES_SAMPLE = 12


def require(cond, message):
    if not cond:
        raise InvariantViolation(message)


def decoded(label, fn, *args):
    try:
        return fn(*args)
    except (ValueError, IndexError, CommandError, UnicodeDecodeError) as exc:
        raise InvariantViolation("%s could not be decoded (%s)" % (label, exc)) from None


def nat_cmp(a, b):
    ta = re.findall(r"[0-9]+|[^0-9]+", a)
    tb = re.findall(r"[0-9]+|[^0-9]+", b)
    for x, y in zip(ta, tb):
        xd, yd = x[0] in "0123456789", y[0] in "0123456789"
        if xd != yd:
            return 1 if xd else -1
        if xd:
            if int(x) != int(y):
                return -1 if int(x) < int(y) else 1
            if len(x) != len(y):
                return -1 if len(x) < len(y) else 1
        elif x != y:
            return -1 if x < y else 1
    return (len(ta) > len(tb)) - (len(ta) < len(tb))


def check_dates(ev):
    days = [ev.start // 86400] + list(ev.skips)
    if ev.rule is not None and ev.rule.until is not None:
        days.append(ev.rule.until)
    for d in days:
        back = civil.days_from_civil(*civil.civil_from_days(d))
        require(back == d, "day %d of %s comes back from the calendar as %d" % (d, ev.id, back))


def check_text(ev):
    require(offsets.parse(offsets.fmt(ev.tz)) == ev.tz,
            "offset %d of %s reads back as %d" % (ev.tz, ev.id, offsets.parse(offsets.fmt(ev.tz))))
    require(decoded("title of " + ev.id, fields.unesc, fields.esc(ev.title)) == ev.title,
            "title of %s is changed by escaping" % ev.id)
    require(fields.split_list(fields.join_list(ev.cats)) == ev.cats,
            "categories of %s are changed by escaping" % ev.id)
    require(fields.normalize_title(ev.title) == ev.title,
            "title of %s changes when normalised again" % ev.id)
    step = 86400 if ev.allday else 60
    require(ev.start % step == 0 and abs(ev.start - ev.raw) <= 30,
            "start of %s moved from %d to %d" % (ev.id, ev.raw, ev.start))


def check_records(ev):
    back = decoded("packed " + ev.id, pack.unpack_event, pack.pack_event(ev))
    require(back.key() == ev.key(), "packed record of %s decodes to a different event" % ev.id)
    data, total = pack.frame([ev])
    again = decoded("frame of " + ev.id, pack.unframe, data, total)
    require(len(again) == 1 and again[0].key() == ev.key(), "frame of %s decodes differently" % ev.id)
    line = textrec.format_record(ev)
    back = decoded("record of " + ev.id, textrec.parse_record, line)
    require(back.full_key() == ev.full_key(), "text record of %s decodes to a different event" % ev.id)


def check_series(ev):
    rule = ev.rule
    require(rules.canon(rule.text()) == rule.text(), "rule of %s is not in canonical form" % ev.id)
    try:
        days = expand.first(ev, SERIES_SAMPLE, with_skips=True)
    except CommandError:
        return
    start = ev.start // 86400
    require(days == sorted(set(days)) and all(d >= start for d in days),
            "series of %s is not increasing" % ev.id)
    if rule.count is not None:
        require(len(days) <= rule.count, "series of %s is longer than its count" % ev.id)
    if rule.until is not None:
        require(all(d <= rule.until for d in days), "series of %s runs past its end" % ev.id)
    if rule.freq == "weekly":
        anchor = civil.week_start(start)
        for d in days:
            require(((d - anchor) // 7) % rule.every == 0,
                    "weekly series of %s has a date outside its weeks" % ev.id)
    if rule.freq == "daily":
        require(all((d - start) % rule.every == 0 for d in days),
                "daily series of %s leaves its step" % ev.id)


def check_skips(ev):
    if not ev.skips:
        return
    require(all(a < b for a, b in zip(ev.skips, ev.skips[1:])), "skips of %s are not increasing" % ev.id)
    require(ev.rule is not None, "%s has skips but no rule" % ev.id)
    live = set(expand.between(ev, ev.skips[0], ev.skips[-1], with_skips=True))
    for d in ev.skips:
        require(d in live, "skip %d of %s is not an occurrence" % (d, ev.id))


def check_ref(seq):
    ref = ids.encode(seq)
    require(decoded("reference " + ref, ids.decode, ref) == seq,
            "reference %s does not read back as %d" % (ref, seq))
    require(ref == "0" or ref[0] != "0", "reference %s of %d has a leading zero" % (ref, seq))
    require(len(ref) <= 10, "reference %s of %d is too long" % (ref, seq))


def check_event(w, ev):
    check_dates(ev)
    check_text(ev)
    check_records(ev)
    check_skips(ev)
    check_ref(ev.seq)
    if ev.rule is not None:
        check_series(ev)


def check_store(w):
    store = w.store
    require(len(store.by_id) == len(store.by_seq), "event tables differ in size")
    for ev in store.by_id.values():
        require(store.by_seq.get(ev.seq) is ev, "event %s is not filed under its number" % ev.id)
        require(ev.seq < store.next_seq, "event %s has a number from the future" % ev.id)
    check_ref(store.next_seq - 1)
    rows = agenda.firsts(store)
    for a, b in zip(rows, rows[1:]):
        ka = (a.utc, -a.ev.prio)
        kb = (b.utc, -b.ev.prio)
        require(ka <= kb, "agenda has %s before %s" % (a.ev.id, b.ev.id))
        if ka == kb:
            require(nat_cmp(a.ev.id, b.ev.id) <= 0,
                    "agenda lists %s before %s at the same time and priority" % (a.ev.id, b.ev.id))


def full_check(w, everything=False):
    store = w.store
    todo = list(store.by_id.values()) if everything else [
        store.by_id[i] for i in sorted(store.dirty) if i in store.by_id]
    for ev in todo:
        check_event(w, ev)
    store.dirty.clear()
    check_store(w)


def cmd_check(w, cmd):
    full_check(w, everything=True)
    w.emit("check ok (%d events)" % len(w.store.by_id))
