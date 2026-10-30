# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Money operations: deposit, withdraw, transfer, capture and reverse.

Every operation validates first and changes state only once it cannot be
refused any more.  Each accepted operation appends exactly one journal
record under a fresh transaction id.
"""
import units
from errors import CommandError, Deny
from journal import Record
from txid import TxId


class Ledger:
    def __init__(self, world):
        self.world = world
        self.denied = 0
        self.replayed = 0

    # ---------------------------------------------------------------- helpers

    def _idem_key(self, acct, key):
        return "%s/%s" % (acct.ident, key)

    def _replayed(self, acct, key):
        if key is None:
            return False
        packed = self.world.idem.lookup(self._idem_key(acct, key))
        if packed is None:
            return False
        self.replayed += 1
        self.world.emit("replay %s" % TxId.from_packed(packed))
        return True

    def _remember(self, acct, key, rec):
        if key is not None:
            self.world.idem.store(self._idem_key(acct, key), rec.tid.packed())

    def _debit_checks(self, acct, amount):
        now = self.world.clock.now
        available = acct.available()
        if amount > available:
            raise Deny("funds", "available=%s" % units.fmt_money(available))
        self.world.limits.check(acct, amount, now)
        if acct.ring.count(now) >= acct.velocity:
            raise Deny("velocity", "limit=%d" % acct.velocity)

    def _count_debit(self, acct, amount):
        now = self.world.clock.now
        self.world.limits.note(acct, amount, now)
        acct.ring.note(now)

    def _post(self, kind, src, dst, amount):
        w = self.world
        rec = Record(w.txids.issue(), kind, src, dst, amount, w.clock.now)
        w.journal.append(rec)
        for acct in (src, dst):
            if acct is not None:
                w.usage.note(acct.slot, w.clock.now)
        return rec

    def deny(self, exc):
        self.denied += 1
        self.world.emit(exc.line())

    # ---------------------------------------------------------------- operations

    def deposit(self, acct, amount, key):
        if self._replayed(acct, key):
            return
        if acct.balance + amount > units.MAX_MONEY:
            raise CommandError("balance too large")
        rec = self._post("deposit", None, acct, amount)
        acct.balance += amount
        self._remember(acct, key, rec)
        self.world.emit("ok %s deposit %s %s balance=%s" % (
            rec.tid, acct.name, units.fmt_money(amount), units.fmt_money(acct.balance)))

    def withdraw(self, acct, amount, key):
        if self._replayed(acct, key):
            return
        self._debit_checks(acct, amount)
        rec = self._post("withdraw", acct, None, amount)
        acct.balance -= amount
        self._count_debit(acct, amount)
        self._remember(acct, key, rec)
        self.world.emit("ok %s withdraw %s %s balance=%s" % (
            rec.tid, acct.name, units.fmt_money(amount), units.fmt_money(acct.balance)))

    def transfer(self, src, dst, amount, key):
        if src is dst:
            raise CommandError("cannot transfer to the same account")
        if self._replayed(src, key):
            return
        if dst.balance + amount > units.MAX_MONEY:
            raise CommandError("balance too large")
        self._debit_checks(src, amount)
        rec = self._post("transfer", src, dst, amount)
        src.balance -= amount
        dst.balance += amount
        self._count_debit(src, amount)
        self._remember(src, key, rec)
        self.world.emit("ok %s transfer %s->%s %s balance=%s" % (
            rec.tid, src.name, dst.name, units.fmt_money(amount), units.fmt_money(src.balance)))

    def capture(self, hold, amount, to):
        owner = hold.owner
        if amount is None:
            amount = hold.amount
        if amount > hold.amount:
            raise CommandError("amount exceeds hold %s" % hold.label)
        if to is owner:
            raise CommandError("cannot capture to the holding account")
        if to is not None and to.balance + amount > units.MAX_MONEY:
            raise CommandError("balance too large")
        self.world.holds.take(hold.ident)
        rec = self._post("capture", owner, to, amount)
        rec.hold = hold.label
        owner.balance -= amount
        if to is not None:
            to.balance += amount
        tail = "" if to is None else " to=%s" % to.name
        self.world.emit("ok %s capture %s %s %s%s" % (
            rec.tid, hold.label, owner.name, units.fmt_money(amount), tail))

    def reverse(self, tid):
        w = self.world
        if not w.txids.issued(tid):
            raise CommandError("unknown transaction %s" % tid)
        rec = w.journal.find(tid)
        if rec is None:
            raise CommandError("%s is compacted" % tid)
        if rec.kind == "reverse":
            raise CommandError("%s is a reversal" % tid)
        if rec.reversed_by is not None:
            raise CommandError("%s already reversed by %s" % (tid, rec.reversed_by))
        debit = self._party(rec.dst, rec.dst_name)
        credit = self._party(rec.src, rec.src_name)
        if credit is not None and credit.balance + rec.amount > units.MAX_MONEY:
            raise CommandError("balance too large")
        new = self._post("reverse", debit, credit, rec.amount)
        new.reverses = rec.tid
        rec.reversed_by = new.tid
        if debit is not None:
            debit.balance -= rec.amount
        if credit is not None:
            credit.balance += rec.amount
        w.emit("ok %s reverse %s %s" % (new.tid, rec.tid, units.fmt_money(rec.amount)))

    def _party(self, ident, name):
        if ident is None:
            return None
        acct = self.world.accounts.live(ident)
        if acct is None:
            raise CommandError("account %s is closed" % name)
        return acct
