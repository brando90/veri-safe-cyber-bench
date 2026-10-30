# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Daily debit limits.

Tallies live in a flat table indexed by slot number so that ``tallies``
reports and the day rollover need no lookups by name.
"""
import units
from errors import Deny


class Tally:
    __slots__ = ("day", "spent")

    def __init__(self):
        self.day = -1
        self.spent = 0


class DailyLimits:
    def __init__(self, size):
        self.table = [Tally() for _ in range(size)]

    def spent_today(self, acct, now):
        t = self.table[acct.slot]
        if t.day != units.day_of(now):
            return 0
        return t.spent

    def check(self, acct, amount, now):
        spent = self.spent_today(acct, now)
        if spent + amount > acct.daily:
            raise Deny("daily", "limit=%s spent=%s" % (units.fmt_money(acct.daily),
                                                      units.fmt_money(spent)))

    def note(self, acct, amount, now):
        t = self.table[acct.slot]
        day = units.day_of(now)
        if t.day != day:
            t.day = day
            t.spent = 0
        t.spent += amount

    def clear_slot(self, idx):
        self.table[idx] = Tally()
