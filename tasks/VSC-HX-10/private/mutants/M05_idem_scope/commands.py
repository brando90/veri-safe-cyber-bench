# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Command handlers.  Each one parses its own arguments, then acts."""
import holds as holds_mod
import invariant
import reports
import txid
import units
from errors import CommandError, Deny


def _amount(cmd, i, what="amount"):
    return units.parse_positive_money(cmd.word(i), what)


def _key(cmd):
    key = cmd.opt("key")
    if key is None:
        return None
    if not key or len(key) > 32 or not all(c.isalnum() or c in "_-" for c in key) \
            or not key.isascii():
        raise CommandError("bad key %s" % key)
    return key


# -------------------------------------------------------------------- clock

def cmd_clock(w, cmd):
    cmd.allow()
    sub = cmd.word(1)
    if sub is None:
        w.emit("now=%d" % w.clock.now)
        return
    cmd.arity(2, 2, "clock [set TIME | advance DURATION]")
    if sub == "set":
        when = w.clock.target(units.parse_duration(cmd.word(2), "time"))
    elif sub == "advance":
        when = w.clock.target_after(units.parse_duration(cmd.word(2)))
    else:
        raise CommandError("usage: clock [set TIME | advance DURATION]")
    w.move_clock(when)


# -------------------------------------------------------------------- accounts

def cmd_open(w, cmd):
    cmd.arity(1, 1, "open NAME [overdraft=AMOUNT] [daily=AMOUNT] [velocity=N]")
    cmd.allow("overdraft", "daily", "velocity")
    overdraft = units.parse_money(cmd.opt("overdraft", "0"), "overdraft")
    daily = units.DEFAULT_DAILY
    if cmd.opt("daily") is not None:
        daily = units.parse_money(cmd.opt("daily"), "daily")
    velocity = units.DEFAULT_VELOCITY
    if cmd.opt("velocity") is not None:
        velocity = units.parse_count(cmd.opt("velocity"), "velocity", 1, units.MAX_VELOCITY)
    acct = w.accounts.open(cmd.word(1), overdraft, daily, velocity)
    w.emit("open %s slot=%d gen=%d" % (acct.name, acct.slot, acct.gen))


def cmd_close(w, cmd):
    cmd.arity(1, 1, "close NAME")
    cmd.allow()
    acct = w.accounts.close(cmd.word(1))
    w.emit("close %s slot=%d" % (acct.name, acct.slot))


def cmd_accounts(w, cmd):
    cmd.arity(0, 0, "accounts")
    cmd.allow()
    rows = w.accounts.sorted()
    for acct in rows:
        w.emit(reports.account_line(w, acct))
    w.emit("accounts open=%d" % len(rows))


def cmd_balance(w, cmd):
    cmd.arity(1, 1, "balance NAME")
    cmd.allow()
    w.emit(reports.balance_line(w, w.accounts.get(cmd.word(1))))


# -------------------------------------------------------------------- money

def cmd_deposit(w, cmd):
    cmd.arity(2, 2, "deposit NAME AMOUNT [key=K]")
    cmd.allow("key")
    acct = w.accounts.get(cmd.word(1))
    w.ledger.deposit(acct, _amount(cmd, 2), _key(cmd))


def cmd_withdraw(w, cmd):
    cmd.arity(2, 2, "withdraw NAME AMOUNT [key=K]")
    cmd.allow("key")
    acct = w.accounts.get(cmd.word(1))
    w.ledger.withdraw(acct, _amount(cmd, 2), _key(cmd))


def cmd_transfer(w, cmd):
    cmd.arity(3, 3, "transfer FROM TO AMOUNT [key=K]")
    cmd.allow("key")
    src = w.accounts.get(cmd.word(1))
    dst = w.accounts.get(cmd.word(2))
    w.ledger.transfer(src, dst, _amount(cmd, 3), _key(cmd))


def cmd_reverse(w, cmd):
    cmd.arity(1, 1, "reverse TXID")
    cmd.allow()
    w.ledger.reverse(txid.parse(cmd.word(1)))


# -------------------------------------------------------------------- holds

def cmd_hold(w, cmd):
    cmd.arity(2, 2, "hold NAME AMOUNT [ttl=DURATION]")
    cmd.allow("ttl")
    acct = w.accounts.get(cmd.word(1))
    amount = _amount(cmd, 2)
    ttl = None
    if cmd.opt("ttl") is not None:
        ttl = units.parse_duration(cmd.opt("ttl"), "ttl")
        if ttl < units.HOLD_TTL_MIN or ttl > units.HOLD_TTL_MAX:
            raise CommandError("ttl out of range")
    hold = w.holds.place(acct, amount, ttl)
    until = "never" if hold.deadline is None else "%d" % hold.deadline
    w.emit("hold %s %s %s until=%s" % (hold.label, acct.name, units.fmt_money(amount), until))


def cmd_capture(w, cmd):
    cmd.arity(1, 1, "capture HOLD [amount=AMOUNT] [to=NAME]")
    cmd.allow("amount", "to")
    hold = w.holds.get(holds_mod.parse_label(cmd.word(1)))
    amount = None
    if cmd.opt("amount") is not None:
        amount = units.parse_positive_money(cmd.opt("amount"))
    to = None
    if cmd.opt("to") is not None:
        to = w.accounts.get(cmd.opt("to"))
    w.ledger.capture(hold, amount, to)


def cmd_release(w, cmd):
    cmd.arity(1, 1, "release HOLD")
    cmd.allow()
    hold = w.holds.take(holds_mod.parse_label(cmd.word(1)))
    w.emit("release %s %s %s" % (hold.label, hold.owner.name, units.fmt_money(hold.amount)))


def cmd_holds(w, cmd):
    cmd.arity(1, 1, "holds NAME")
    cmd.allow()
    acct = w.accounts.get(cmd.word(1))
    rows = w.holds.of(acct)
    for hold in rows:
        w.emit(reports.hold_line(hold))
    w.emit("holds %s count=%d held=%s" % (acct.name, len(rows), units.fmt_money(acct.held)))


# -------------------------------------------------------------------- journal

def cmd_show(w, cmd):
    cmd.arity(1, 1, "show TXID")
    cmd.allow()
    tid = txid.parse(cmd.word(1))
    if not w.txids.issued(tid):
        raise CommandError("unknown transaction %s" % tid)
    rec = w.journal.find(tid)
    if rec is None:
        w.emit("%s compacted" % tid)
        return
    w.emit(reports.record_line(rec))


def cmd_history(w, cmd):
    cmd.arity(1, 1, "history NAME [last=N]")
    cmd.allow("last")
    acct = w.accounts.get(cmd.word(1))
    last = 10
    if cmd.opt("last") is not None:
        last = units.parse_count(cmd.opt("last"), "last", 1, 1000)
    rows = w.journal.history(acct.ident, last)
    for rec in rows:
        w.emit(reports.record_line(rec))
    if not rows:
        w.emit("history %s empty" % acct.name)


def cmd_journal(w, cmd):
    cmd.arity(0, 0, "journal")
    cmd.allow()
    w.emit(reports.journal_line(w.journal))


# -------------------------------------------------------------------- settlement

def cmd_settle(w, cmd):
    cmd.arity(0, 0, "settle")
    cmd.allow()
    w.settlement.settle()


def cmd_clearing(w, cmd):
    cmd.allow()
    if cmd.word(1) is None:
        w.emit(reports.clearing_line(w.clearing))
        return
    cmd.arity(2, 2, "clearing [fail N]")
    if cmd.word(1) != "fail":
        raise CommandError("usage: clearing [fail N]")
    w.clearing.script_failures(units.parse_count(cmd.word(2), "count", 0, 1000))
    w.emit(reports.clearing_line(w.clearing))


def cmd_batches(w, cmd):
    cmd.arity(0, 0, "batches [last=N]")
    cmd.allow("last")
    last = 10
    if cmd.opt("last") is not None:
        last = units.parse_count(cmd.opt("last"), "last", 1, 1000)
    rows = w.settlement.batches[-last:]
    for batch in rows:
        w.emit(w.settlement.describe(batch))
    w.emit("batches total=%d pending=%d unassigned=%d" % (
        len(w.settlement.batches), len(w.settlement.pending()),
        w.journal.next_index - w.settlement.next_unassigned))


# -------------------------------------------------------------------- misc

def cmd_idem(w, cmd):
    cmd.arity(0, 0, "idem")
    cmd.allow()
    w.emit(reports.idem_line(w.idem))


def cmd_check(w, cmd):
    cmd.arity(0, 0, "check")
    cmd.allow()
    invariant.full(w)
    w.emit("check ok records=%d live=%d accounts=%d holds=%d batches=%d" % (
        w.journal.next_index, w.journal.live_count, len(w.accounts), len(w.holds),
        len(w.settlement.batches)))


TABLE = {
    "clock": cmd_clock,
    "open": cmd_open,
    "close": cmd_close,
    "accounts": cmd_accounts,
    "balance": cmd_balance,
    "deposit": cmd_deposit,
    "withdraw": cmd_withdraw,
    "transfer": cmd_transfer,
    "reverse": cmd_reverse,
    "hold": cmd_hold,
    "capture": cmd_capture,
    "release": cmd_release,
    "holds": cmd_holds,
    "show": cmd_show,
    "history": cmd_history,
    "journal": cmd_journal,
    "settle": cmd_settle,
    "clearing": cmd_clearing,
    "batches": cmd_batches,
    "idem": cmd_idem,
    "check": cmd_check,
}


def run(w, cmd):
    handler = TABLE.get(cmd.name)
    if handler is None:
        raise CommandError("unknown command %s" % cmd.name)
    try:
        handler(w, cmd)
    except Deny as exc:
        w.ledger.deny(exc)
