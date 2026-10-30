# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Accounts and the registry of open accounts."""
import re

import units
from errors import CommandError
from velocity import MinuteRing

NAME_RE = re.compile(r"[a-z][a-z0-9_]{0,15}")


class Account:
    __slots__ = ("name", "slot", "gen", "ident", "balance", "held", "holds", "overdraft",
                 "daily", "velocity", "ring", "opened_at")

    def __init__(self, name, slot, gen, overdraft, daily, velocity, now):
        self.name = name
        self.slot = slot
        self.gen = gen
        self.ident = "%d.%d" % (slot, gen)
        self.balance = 0
        self.held = 0
        self.holds = set()
        self.overdraft = overdraft
        self.daily = daily
        self.velocity = velocity
        self.ring = MinuteRing(units.RING_MINUTES)
        self.opened_at = now

    def available(self):
        return self.balance + self.overdraft - self.held


class Registry:
    def __init__(self, world):
        self.world = world
        self.by_name = {}
        self.by_ident = {}

    def __len__(self):
        return len(self.by_name)

    def get(self, name):
        acct = self.by_name.get(name)
        if acct is None:
            raise CommandError("unknown account %s" % name)
        return acct

    def live(self, ident):
        return self.by_ident.get(ident)

    def open(self, name, overdraft, daily, velocity):
        if NAME_RE.fullmatch(name) is None:
            raise CommandError("bad account name %s" % name)
        if name in self.by_name:
            raise CommandError("account %s exists" % name)
        slot, gen = self.world.slots.take()
        acct = Account(name, slot, gen, overdraft, daily, velocity, self.world.clock.now)
        self.by_name[name] = acct
        self.by_ident[acct.ident] = acct
        return acct

    def close(self, name):
        acct = self.get(name)
        if acct.holds:
            raise CommandError("account %s has holds" % name)
        if acct.balance != 0:
            raise CommandError("account %s balance not zero" % name)
        self.world.slots.give_back(acct.slot)
        self.world.idem.forget_prefix(acct.ident + "/")
        del self.by_name[name]
        del self.by_ident[acct.ident]
        return acct

    def sorted(self):
        return [self.by_name[n] for n in sorted(self.by_name)]
