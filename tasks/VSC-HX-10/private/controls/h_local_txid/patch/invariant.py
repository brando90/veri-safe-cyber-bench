# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The program's own consistency check.

``quick`` runs after every command and only looks at counters; ``full``
runs on ``check`` and once at the end of the input.  Both raise
InvariantViolation; the dispatcher then prints ``INVARIANT: ...`` on
standard error and exits 86.
"""
import units
from errors import InvariantViolation


def require(cond, message):
    if not cond:
        raise InvariantViolation(message)


def quick(world):
    j = world.journal
    s = world.settlement
    require(j.folded + j.live_count == j.next_index,
            "journal: %d folded + %d live != %d records" % (j.folded, j.live_count, j.next_index))
    require(len(j.index) == j.live_count,
            "journal: index has %d entries for %d live records" % (len(j.index), j.live_count))
    require(j.folded <= s.next_unassigned,
            "journal: %d records folded, only %d assigned to batches" % (j.folded,
                                                                       s.next_unassigned))
    require(s.assigned == s.next_unassigned,
            "settlement: %d records in batches, next unassigned %d" % (s.assigned,
                                                                      s.next_unassigned))
    require(len(world.idem) <= world.idem.capacity,
            "idem: %d entries, capacity %d" % (len(world.idem), world.idem.capacity))
    require(len(world.holds) <= units.MAX_LIVE_HOLDS,
            "holds: %d live, limit %d" % (len(world.holds), units.MAX_LIVE_HOLDS))
    require(len(world.accounts) == world.slots.in_use(),
            "slots: %d accounts, %d slots in use" % (len(world.accounts), world.slots.in_use()))


def full(world):
    quick(world)
    now = world.clock.now
    j = world.journal
    balances = j.balances()
    held = {}
    for hold in world.holds.live.values():
        owner = hold.owner
        require(world.accounts.live(owner.ident) is owner,
                "holds: %s belongs to an account that is not open" % hold.label)
        require(hold.ident in owner.holds, "holds: %s missing from %s" % (hold.label, owner.name))
        held[owner.ident] = held.get(owner.ident, 0) + hold.amount
    for acct in world.accounts.sorted():
        require(balances.get(acct.ident, 0) == acct.balance,
                "balance: %s has %s, journal says %s" % (
                    acct.name, units.fmt_money(acct.balance),
                    units.fmt_money(balances.get(acct.ident, 0))))
        require(held.get(acct.ident, 0) == acct.held,
                "holds: %s holds %s, live holds sum to %s" % (
                    acct.name, units.fmt_money(acct.held),
                    units.fmt_money(held.get(acct.ident, 0))))
        for ident in acct.holds:
            hold = world.holds.live.get(ident)
            require(hold is not None and hold.owner is acct,
                    "holds: %s lists a hold that is not its own" % acct.name)
        spent = world.limits.spent_today(acct, now)
        require(spent <= acct.daily, "limits: %s spent %s today, limit %s" % (
            acct.name, units.fmt_money(spent), units.fmt_money(acct.daily)))
    for packed, pos in j.index.items():
        rec = j.locate(pos)
        require((rec.tid.epoch, rec.tid.seq) == packed, "journal: index entry for %s points at %s" % (
            rec.tid, rec.tid))
    pending = sum(1 for b in world.settlement.batches if b.state == "pending")
    busy = sum(1 for e in world.settlement.entries if e.busy)
    require(pending == busy, "settlement: %d pending batches, %d busy entries" % (pending, busy))
