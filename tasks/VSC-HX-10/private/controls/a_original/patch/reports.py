# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Text formats of records, accounts, holds and summaries."""
import units


def parties(rec):
    return "%s->%s" % (rec.src_name or "", rec.dst_name or "")


def record_line(rec):
    parts = [str(rec.tid), rec.kind, parties(rec), units.fmt_money(rec.amount), "at=%d" % rec.at]
    if rec.hold is not None:
        parts.append("hold=%s" % rec.hold)
    if rec.reverses is not None:
        parts.append("reverses=%s" % rec.reverses)
    if rec.reversed_by is not None:
        parts.append("reversed_by=%s" % rec.reversed_by)
    return " ".join(parts)


def account_line(world, acct):
    return "%s slot=%d gen=%d balance=%s held=%s ops=%d" % (
        acct.name, acct.slot, acct.gen, units.fmt_money(acct.balance), units.fmt_money(acct.held),
        world.usage.ops_of(acct.slot))


def balance_line(world, acct):
    now = world.clock.now
    return "%s balance=%s held=%s available=%s spent_today=%s debits_last_hour=%d" % (
        acct.name, units.fmt_money(acct.balance), units.fmt_money(acct.held),
        units.fmt_money(acct.available()), units.fmt_money(world.limits.spent_today(acct, now)),
        acct.ring.count(now))


def hold_line(hold):
    until = "never" if hold.deadline is None else "%d" % hold.deadline
    return "%s %s %s until=%s" % (hold.label, hold.owner.name, units.fmt_money(hold.amount), until)


def journal_line(journal):
    return "journal records=%d folded=%d live=%d segments=%d sealed=%d compactions=%d" % (
        journal.next_index, journal.folded, journal.live_count, len(journal.segments),
        journal.sealed_count(), journal.compactions)


def idem_line(idem):
    return "idem entries=%d capacity=%d evicted=%d" % (len(idem), idem.capacity, idem.evicted)


def clearing_line(clearing):
    return "clearing fail_next=%d submitted=%d accepted=%d" % (
        clearing.fail_next, clearing.submitted, clearing.accepted)
