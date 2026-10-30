# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""``explain ID``: why a pending message is not being attempted right now.

This is a diagnostic for operators.  It evaluates the same rules as the
dispatcher (dispatch.Dispatcher.eligible) for each unacknowledged fragment
of the message, at the current instant, but reports every reason that
applies instead of stopping at the first one.  It never changes state.
"""

import localtime
import timefmt


def _quiet_reason(svc, msg, now):
    if msg.prio == "urgent":
        return None
    window = svc.cfg.quiet(msg.recipient)
    offset = svc.offset_of(msg.recipient)
    if not localtime.in_quiet(now, offset, window):
        return None
    return "quiet hours until %s local" % timefmt.fmt_hhmm(window[1])


def _limit_reason(svc, msg, now):
    if msg.started:
        return None
    r = msg.recipient
    reason = svc.limits.block_reason(svc.cfg, r, svc.offset_of(r), now, msg.size)
    if reason is None:
        return None
    return "limit %s" % reason


def reasons_for(svc, msg, frag, now):
    out = []
    if frag.not_before > now:
        out.append("next attempt at %s" % timefmt.fmt_instant(frag.not_before))
    if svc.breaker.paused(msg.recipient):
        out.append("recipient paused until %s"
                   % timefmt.fmt_instant(svc.breaker.paused_until(msg.recipient)))
    q = _quiet_reason(svc, msg, now)
    if q:
        out.append(q)
    lim = _limit_reason(svc, msg, now)
    if lim:
        out.append(lim)
    return out


def lines(svc, msg):
    if not msg.pending:
        return ["explain %s: %s" % (msg.id, msg.state)]
    now = svc.now
    out = ["explain %s at %s: deadline %s" % (msg.id, timefmt.fmt_instant(now),
                                               timefmt.fmt_instant(msg.deadline))]
    for frag in msg.unacked():
        why = reasons_for(svc, msg, frag, now)
        label = frag.label(len(msg.frags))
        if why:
            out.append("fragment %s waits: %s" % (label, "; ".join(why)))
        else:
            out.append("fragment %s ready for the next round" % label)
    return out
