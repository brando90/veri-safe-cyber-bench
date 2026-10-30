# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Wiring: one World owns every component of a run."""
import commands
import units
from accounts import Registry
from clearing import Clearing
from clock import Clock
from holds import HoldBook
from idem import IdemCache
from journal import Journal
from ledger import Ledger
from limits import DailyLimits
from settlement import Settlement
from slots import SlotTable
from stats import UsageCounters
from timers import Wheel
from txid import TxIdGen


class World:
    def __init__(self, out):
        self.out = out
        self.clock = Clock()
        self.slots = SlotTable(units.SLOTS)
        self.usage = UsageCounters(units.SLOTS)
        self.limits = DailyLimits(units.SLOTS)
        self.accounts = Registry(self)
        self.txids = TxIdGen()
        self.timers = Wheel(units.WHEEL_SECONDS)
        self.holds = HoldBook(self)
        self.idem = IdemCache(units.IDEM_CAPACITY)
        self.clearing = Clearing()
        self.settlement = Settlement(self)
        self.journal = Journal(self)
        self.ledger = Ledger(self)
        self.slots.recycle_hooks.append(self.usage.clear_slot)
        self.slots.recycle_hooks.append(self.limits.clear_slot)
        self.commands_run = 0

    def emit(self, line):
        self.out.emit(line)

    def dispatch(self, cmd):
        self.commands_run += 1
        commands.run(self, cmd)

    def move_clock(self, when):
        """Move the clock, then let holds expire and due settlement retries run."""
        self.clock.move(when)
        self.emit("now=%d" % when)
        for hold in self.holds.expire_due(when):
            self.emit("expire %s %s %s" % (hold.label, hold.owner.name,
                                           units.fmt_money(hold.amount)))
        self.settlement.on_clock(when)
