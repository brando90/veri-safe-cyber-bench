# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The event model and the store that holds the events."""
import expand
import ids
import names
from errors import CommandError


class Event:
    __slots__ = ("id", "seq", "title", "start", "raw", "dur", "rule", "tz", "allday",
                 "prio", "cats", "skips")

    def __init__(self, eid, seq, title, start, raw, dur, rule, tz, allday, prio, cats, skips):
        self.id = eid
        self.seq = seq
        self.title = title
        self.start = start
        self.raw = raw
        self.dur = dur
        self.rule = rule
        self.tz = tz
        self.allday = allday
        self.prio = prio
        self.cats = list(cats)
        self.skips = list(skips)

    def key(self):
        return (self.id, self.seq, self.title, self.start, self.dur,
                self.rule.text() if self.rule else "", self.tz, self.allday, self.prio,
                tuple(self.cats), tuple(self.skips))

    def full_key(self):
        return self.key() + (self.raw,)

    def utc(self, day):
        """UTC instant of the occurrence on local date DAY (all-day events float)."""
        local = day * 86400 + self.start % 86400
        return local if self.allday else local - self.tz * 60

    def clone(self):
        return Event(self.id, self.seq, self.title, self.start, self.raw, self.dur, self.rule,
                     self.tz, self.allday, self.prio, self.cats, self.skips)


def drop_stale_skips(ev):
    if not ev.skips:
        return
    if ev.rule is None:
        ev.skips = []
        return
    try:
        live = set(expand.between(ev, ev.skips[0], ev.skips[-1], with_skips=True))
    except CommandError:
        live = set()
    ev.skips = [d for d in ev.skips if d in live or d == ev.skips[-1]]


def reschedule(ev, start, raw, rule):
    ev.start, ev.raw, ev.rule = start, raw, rule
    drop_stale_skips(ev)


class Store:
    def __init__(self):
        self.by_id = {}
        self.by_seq = {}
        self.next_seq = 1
        self.dirty = set()
        self.first_day = {}

    def ordered(self):
        return [self.by_seq[s] for s in sorted(self.by_seq)]

    def touch(self, ev):
        self.dirty.add(ev.id)
        self.first_day.pop(ev.id, None)

    def find(self, token):
        """The event named by TOKEN: an id, or ``#`` and a base-32 reference."""
        if token.startswith("#"):
            try:
                seq = ids.decode(token[1:])
            except ValueError:
                raise CommandError("bad_ref", token) from None
            ev = self.by_seq.get(seq)
        else:
            ev = self.by_id.get(token)
        if ev is None:
            raise CommandError("unknown_event", token)
        return ev

    def allocate(self, requested):
        """(id, seq) for a new event; REQUESTED is an id or None for an automatic one."""
        if requested is not None:
            names.check_id(requested)
            if requested in self.by_id:
                raise CommandError("event_exists", requested)
        seq = self.next_seq
        while True:
            if seq > ids.MAX_SEQ:
                raise CommandError("seq_exhausted")
            if requested is not None or "E" + ids.encode(seq) not in self.by_id:
                break
            seq += 1
        return (requested if requested is not None else "E" + ids.encode(seq)), seq

    def insert(self, ev):
        if ev.id in self.by_id or ev.seq in self.by_seq:
            raise CommandError("event_exists", ev.id)
        self.by_id[ev.id] = ev
        self.by_seq[ev.seq] = ev
        self.next_seq = max(self.next_seq, ev.seq + 1)
        self.touch(ev)

    def remove(self, ev):
        del self.by_id[ev.id]
        del self.by_seq[ev.seq]
        self.dirty.discard(ev.id)
        self.first_day.pop(ev.id, None)
