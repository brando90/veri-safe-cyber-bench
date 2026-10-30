# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Text of the listing commands: queue, show, inbox, config, invoice, plans."""

import billing
import config
import localtime
import money
import retry
import timefmt


def queue_lines(svc):
    entries = svc.queue.ordered()
    out = ["queue at %s: %d entries" % (timefmt.fmt_instant(svc.now), len(entries))]
    for e in entries:
        m, f = e.msg, e.frag
        out.append("%s %s %s->%s prio=%s attempts=%d not-before=%s" % (
            m.id, f.label(len(m.frags)), m.sender, m.recipient, m.prio, f.attempts,
            timefmt.fmt_instant(f.not_before)))
    return out


def _when(t):
    return "-" if t is None else timefmt.fmt_instant(t)


def show_lines(msg):
    out = ["message %s %s->%s prio=%s state=%s size=%d frags=%d via=%s" % (
        msg.id, msg.sender, msg.recipient, msg.prio, msg.state, msg.size,
        len(msg.frags), msg.via),
        "accepted=%s deadline=%s started=%s finished=%s" % (
            _when(msg.accepted_at), _when(msg.deadline), _when(msg.received_at),
            _when(msg.finished_at))]
    for f in msg.frags:
        out.append("fragment %s bytes=%d attempts=%d acked=%s" % (
            f.label(len(msg.frags)), len(f.data), f.attempts, "yes" if f.acked else "no"))
    return out


def inbox_lines(rcpt):
    out = ["inbox %s: %d messages" % (rcpt.name, len(rcpt.inbox))]
    for msg_id, sender, body in rcpt.inbox:
        out.append("%s from %s: %s" % (msg_id, sender, body))
    return out


def config_lines(svc, recipient=None):
    head = "config" if recipient is None else "config for " + recipient
    out = [head]
    for key, value, source in svc.cfg.rows(recipient):
        out.append("%s %s %s %s" % (key, value, config.KEYS[key].unit, source))
    return out


def invoice_lines(svc, sender, number, lines):
    plan = svc.senders[sender].plan
    out = ["invoice %s #%d plan=%s" % (sender, number, plan)]
    for l in lines:
        out.append("%s %s %s size=%d prio=%s %s" % (
            l.msg_id, timefmt.fmt_instant(l.at), l.recipient, l.size, l.prio,
            money.fmt(l.cents())))
    out.append("total=%s lines=%d" % (money.fmt(sum(l.cents() for l in lines)),
                                      len(lines)))
    return out


def plan_lines(svc):
    out = []
    for name in sorted(billing.PLANS):
        out.append("plan %s messages=%d revenue=%s" % (
            name, svc.billing.count(name), money.fmt(money.total(svc.billing.amounts(plan=name)))))
    out.append("all messages=%d revenue=%s" % (
        svc.billing.count(), money.fmt(money.total(svc.billing.amounts()))))
    return out


def daily_lines(svc, rcpt):
    """Deliveries to RCPT per local day of completion."""
    days = {}
    for m in svc.messages.values():
        if m.recipient != rcpt.name or m.state != "delivered":
            continue
        day = localtime.local_day(m.finished_at, rcpt.offset_min)
        d = days.setdefault(day, [0, 0])
        d[0] += 1
        d[1] += m.size
    out = ["daily %s tz=%s" % (rcpt.name, timefmt.fmt_offset(rcpt.offset_min))]
    for day in sorted(days):
        out.append("local-day %d delivered=%d bytes=%d" % (day, days[day][0], days[day][1]))
    return out


def sender_lines(svc):
    """Senders by revenue (highest first), then by name."""
    rows = []
    for name, s in svc.senders.items():
        amounts = svc.billing.amounts(sender=name)
        rows.append((-money.total(amounts), name, s.plan, len(amounts)))
    rows.sort()
    out = ["senders"]
    for neg, name, plan, count in rows:
        last = svc.queue.last_served_at(name)
        out.append("sender %s plan=%s delivered=%d revenue=%s last-attempt=%s" % (
            name, plan, count, money.fmt(-neg), "-" if last is None else timefmt.fmt_instant(last)))
    return out


def retry_lines(svc):
    """The global backoff table: delay after the n-th failed attempt."""
    cfg = svc.cfg
    n_max = cfg.get("retry.max_attempts")
    out = ["retry max_attempts=%d" % n_max]
    for n, delay in enumerate(retry.schedule_text(cfg, n_max), 1):
        out.append("after-failure %d wait=%s" % (n, timefmt.fmt_seconds(delay)))
    return out
