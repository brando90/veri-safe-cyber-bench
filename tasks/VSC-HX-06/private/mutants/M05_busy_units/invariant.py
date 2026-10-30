# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""relaydesk's documented invariants (README, "Invariants").

Any failure raises InvariantError; main.py prints ``INVARIANT: <reason>``
on stderr and exits with status 86.
"""

import model
from errors import InvariantError


def check_capacity(svc, recipient):
    """Called right after a message is accepted."""
    cap = svc.cfg.get("queue.max_pending", recipient)
    n = svc.pending_for(recipient)
    if n > cap:
        raise InvariantError("recipient %s has %d pending messages, limit %d"
                             % (recipient, n, cap))


def check_reassembly(msg, data):
    """Called when a message is complete at its recipient."""
    if len(data) != msg.size:
        raise InvariantError("message %s reassembled to %d bytes, expected %d"
                             % (msg.id, len(data), msg.size))


def check_all(svc):
    """Called after every command."""
    c = svc.stats.c
    by_state = {s: 0 for s in (model.PENDING,) + model.FINAL_STATES}
    for m in svc.messages.values():
        by_state[m.state] += 1
    if c["accepted"] != len(svc.messages):
        raise InvariantError("accepted counter %d, messages %d" % (c["accepted"], len(svc.messages)))
    for state, counter in ((model.DELIVERED, "delivered"), (model.FAILED, "failed"),
                           (model.EXPIRED, "expired"), (model.CANCELLED, "cancelled")):
        if by_state[state] != c[counter]:
            raise InvariantError("%s counter %d, messages %d" % (counter, c[counter], by_state[state]))
    if svc.queue.services() != c["attempts"]:
        raise InvariantError("queue counted %d attempts, statistics %d"
                             % (svc.queue.services(), c["attempts"]))
    per = sum(r["delivered"] for r in svc.stats.per.values())
    if per != c["delivered"]:
        raise InvariantError("per-recipient deliveries %d, total %d" % (per, c["delivered"]))
    if len(svc.billing.lines) != c["delivered"]:
        raise InvariantError("billing lines %d, deliveries %d" % (len(svc.billing.lines), c["delivered"]))
    for entry in svc.queue.entries():
        if not entry.msg.pending or entry.frag.acked:
            raise InvariantError("stale queue entry %s/%d" % (entry.msg.id, entry.frag.index))
    for m in svc.messages.values():
        if m.pending and not m.unacked() and m.buffer is not None and not m.buffer.missing():
            raise InvariantError("message %s complete but still pending" % m.id)
