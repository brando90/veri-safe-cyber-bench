# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The dispatcher: dispatch rounds, attempts, retries, expiry, completion.

Dispatch rounds happen at every multiple of ``dispatch.interval_ms`` on
the logical clock.  Moving the clock from NOW to T runs every round in
(NOW, T], in order.  A round at instant t:

1. ends the pauses that are over (RESUME);
2. expires pending messages whose deadline is <= t (EXPIRE), in
   acceptance order;
3. makes up to ``dispatch.batch`` attempts, each time on the best
   eligible queue entry (queueing.py).

Rounds in which nothing can change are skipped: when a round does
nothing, the next round considered is the first one at or after the
earliest instant at which some rule can give a different answer.
"""

import invariant
import localtime
import model
import money
import retry
import timefmt
import units


class Dispatcher:
    def __init__(self, svc):
        self.svc = svc
        svc.dispatcher = self

    # ------------------------------------------------------------ clock
    def _interval(self):
        return self.svc.cfg.get("dispatch.interval_ms")

    def round_after(self, t):
        iv = self._interval()
        return (t // iv + 1) * iv

    def round_at_or_after(self, t):
        iv = self._interval()
        return -(-t // iv) * iv

    def run_until(self, target):
        svc = self.svc
        nxt = self.round_after(svc.now)
        while nxt <= target and svc.pending():
            svc.now = nxt
            if self.round(nxt):
                nxt = self.round_after(nxt)
            else:
                nxt = max(self.round_at_or_after(self.wakeup(nxt)), self.round_after(nxt))
        svc.now = target

    def wakeup(self, t):
        """Earliest instant after T at which a pending message may change."""
        svc = self.svc
        # Quiet hours and local days change only on whole minutes.
        cands = [(t // units.MS_PER_MIN + 1) * units.MS_PER_MIN]
        busy = set()
        for msg in svc.pending():
            busy.add(msg.recipient)
            cands.append(msg.deadline)
            for frag in msg.frags:
                if not frag.acked and frag.not_before > t:
                    cands.append(frag.not_before)
        cands.extend(svc.breaker.wakeups(t))
        for r in sorted(busy):
            cands.extend(svc.limits.wakeups(r, t))
        return min(c for c in cands if c > t)

    # ------------------------------------------------------------ rounds
    def round(self, t):
        svc = self.svc
        active = False
        for r in svc.breaker.due(t):
            svc.event(t, "RESUME %s" % r)
            svc.audit.add(t, "resume", ("recipient", r))
            active = True
        for msg in svc.pending():
            if t >= msg.deadline:
                self.expire(msg, t)
                active = True
        counts = {}
        made = 0
        batch = svc.cfg.get("dispatch.batch")
        while made < batch:
            entry = svc.queue.best(lambda e: self.eligible(e, t, counts))
            if entry is None:
                break
            self.attempt(entry, t, counts)
            made += 1
        return active or made > 0

    def eligible(self, entry, t, counts):
        svc = self.svc
        cfg = svc.cfg
        msg, frag = entry.msg, entry.frag
        if not msg.pending or frag.acked or frag.not_before > t:
            return False
        r = msg.recipient
        if svc.breaker.paused(r):
            return False
        if counts.get(r, 0) >= cfg.get("dispatch.per_recipient", r):
            return False
        offset = svc.offset_of(r)
        if msg.prio != "urgent" and localtime.in_quiet(t, offset, cfg.quiet(r)):
            return False
        if not msg.started and svc.limits.block_reason(cfg, r, offset, t, msg.size):
            return False
        return True

    # ------------------------------------------------------------ attempts
    def attempt(self, entry, t, counts):
        r = entry.msg.recipient
        counts[r] = counts.get(r, 0) + 1
        outcome = self.begin(entry, t)
        if outcome.acked:
            self.svc.breaker.on_success(r)
        self.settle(entry, t, outcome, direct=False)

    def begin(self, entry, t):
        """Make one attempt of ENTRY's fragment at T; returns the outcome."""
        svc = self.svc
        entry.frag.attempts += 1
        svc.stats.bump("attempts")
        svc.queue.mark_served(entry.msg.sender, t)
        return svc.links.next(entry.msg.recipient)

    def settle(self, entry, t, outcome, direct):
        """Apply OUTCOME of the attempt just made on ENTRY."""
        svc = self.svc
        cfg = svc.cfg
        msg, frag = entry.msg, entry.frag
        r = msg.recipient
        complete = False
        if outcome.arrived:
            if not msg.started:
                msg.received_at = t
                svc.limits.record(r, svc.offset_of(r), t, msg.size)
            complete = msg.buffer.add(frag.index, frag.data)
        svc.note(msg, t, "SEND %s %s %s->%s %s%s" % (
            msg.id, frag.label(len(msg.frags)), msg.sender, r, outcome.word(),
            " direct" if direct else ""))
        if outcome.acked:
            frag.acked = True
            svc.queue.take(entry)
        else:
            until = svc.breaker.on_failure(r, t, cfg.get("breaker.threshold", r),
                                           cfg.ms("breaker.pause_s", r))
            if until is not None:
                svc.event(t, "PAUSE %s until %s" % (r, _fmt(until)))
                svc.audit.add(t, "pause", ("recipient", r), ("until", _stamp(until)))
            if not complete:
                hint = units.s_to_ms(outcome.after_s)
                decision = retry.decide(cfg, msg, frag, t, hint)
                if decision.kind == retry.FAIL:
                    self.fail(msg, frag, t)
                elif decision.kind == retry.EXPIRE:
                    self.expire(msg, t)
                else:
                    frag.not_before = decision.at
                    svc.queue.take(entry)
                    svc.queue.add(msg, frag)
                    svc.stats.bump("retries")
                    svc.note(msg, t, "RETRY %s %s at %s" % (
                        msg.id, frag.label(len(msg.frags)), _fmt(decision.at)))
        if complete:
            self.finish(msg, t)

    # ------------------------------------------------------------ final states
    def finish(self, msg, t):
        svc = self.svc
        data = msg.buffer.assemble()
        invariant.check_reassembly(msg, data)
        msg.state = model.DELIVERED
        msg.finished_at = t
        svc.queue.drop_message(msg.id)
        svc.recipients[msg.recipient].inbox.append((msg.id, msg.sender, data.decode("utf-8")))
        svc.stats.on_delivered(msg, t)
        line = svc.billing.charge(msg, svc.senders[msg.sender].plan, t)
        svc.note(msg, t, "DONE %s %s->%s size=%d cost=%s" % (
            msg.id, msg.sender, msg.recipient, msg.size, money.fmt(line.cents())))

    def fail(self, msg, frag, t):
        svc = self.svc
        self._close(msg, model.FAILED, t)
        svc.stats.bump("failed")
        svc.note(msg, t, "FAIL %s %s attempts=%d" % (msg.id, frag.label(len(msg.frags)), frag.attempts))

    def expire(self, msg, t):
        svc = self.svc
        self._close(msg, model.EXPIRED, t)
        svc.stats.bump("expired")
        svc.note(msg, t, "EXPIRE %s" % msg.id)

    def cancel(self, msg, t):
        svc = self.svc
        self._close(msg, model.CANCELLED, t)
        svc.stats.bump("cancelled")
        svc.note(msg, t, "CANCEL %s" % msg.id)

    def _close(self, msg, state, t):
        msg.state = state
        msg.finished_at = t
        msg.buffer = None
        self.svc.queue.drop_message(msg.id)


def _fmt(t):
    return timefmt.fmt_instant(t)


def _stamp(t):
    """Instant as one token (audit values contain no blanks)."""
    return _fmt(t).replace(" ", "/")
