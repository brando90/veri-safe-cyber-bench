# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Holds: funds reserved on an account until captured, released or expired."""
import units
from errors import CommandError, Deny, InvariantViolation

_HOLD_RE_PREFIX = "H"


class Hold:
    __slots__ = ("ident", "owner", "amount", "deadline", "placed_at")

    def __init__(self, ident, owner, amount, deadline, placed_at):
        self.ident = ident
        self.owner = owner
        self.amount = amount
        self.deadline = deadline
        self.placed_at = placed_at

    @property
    def label(self):
        return label(self.ident)


def label(ident):
    return "H%03d" % ident


def parse_label(text):
    if not text or not text.startswith(_HOLD_RE_PREFIX) or not text[1:].isdigit() \
            or len(text) != 4:
        raise CommandError("bad hold id %s" % text)
    ident = int(text[1:])
    if ident < 1 or ident > units.HOLD_ID_MAX:
        raise CommandError("bad hold id %s" % text)
    return ident


class HoldBook:
    def __init__(self, world):
        self.world = world
        self.live = {}
        self.cursor = 0
        self.placed = 0
        self.expired = 0

    def __len__(self):
        return len(self.live)

    def _next_id(self):
        for _ in range(units.HOLD_ID_MAX):
            self.cursor = self.cursor % units.HOLD_ID_MAX + 1
            if not self.world.timers.pending(self.cursor):
                return self.cursor
        raise InvariantViolation("holds: no free hold id with %d live holds" % len(self.live))

    def get(self, ident):
        hold = self.live.get(ident)
        if hold is None:
            raise CommandError("unknown hold %s" % label(ident))
        return hold

    def place(self, acct, amount, ttl):
        if len(self.live) >= units.MAX_LIVE_HOLDS:
            raise CommandError("too many holds")
        available = acct.available()
        if amount > available:
            raise Deny("funds", "available=%s" % units.fmt_money(available))
        now = self.world.clock.now
        ident = self._next_id()
        deadline = None if ttl is None else now + ttl
        hold = Hold(ident, acct, amount, deadline, now)
        self.live[ident] = hold
        acct.holds.add(ident)
        acct.held += amount
        if deadline is not None:
            self.world.timers.schedule(ident, deadline)
        self.placed += 1
        return hold

    def take(self, ident):
        hold = self.get(ident)
        del self.live[ident]
        hold.owner.holds.discard(ident)
        hold.owner.held -= hold.amount
        self.world.timers.cancel(ident)
        return hold

    def expire_due(self, now):
        gone = []
        for _deadline, ident in self.world.timers.due(now):
            if ident in self.live:
                gone.append(self.take(ident))
                self.expired += 1
        return gone

    def of(self, acct):
        return sorted((h for h in self.live.values() if h.owner is acct), key=lambda h: h.ident)
