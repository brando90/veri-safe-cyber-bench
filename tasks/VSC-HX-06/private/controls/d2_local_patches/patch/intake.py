# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Accepting messages (README, "Sending").

Both entry points, ``send`` and ``batch``, build a Request and hand it to
submit(), which applies the checks in the documented order:

1. the id is not in use and the sender and recipient exist;
2. duplicate detection (DUP);
3. capacity: fewer than ``queue.max_pending`` messages pending for the
   recipient (REJECT queue-full);
4. acceptance: TTL, fragments, queue entries, ACCEPT;
5. the direct attempt for urgent single-fragment messages.
"""

import fragment
import invariant
import model
import reassembly
import timefmt
from errors import CommandError

SEND_OPTIONS = ("prio", "ttl", "after")


class Request:
    __slots__ = ("id", "sender", "recipient", "prio", "ttl_ms", "after_ms", "text", "via")

    def __init__(self, msg_id, sender, recipient, opts, text, via):
        self.id = msg_id
        self.sender = sender
        self.recipient = recipient
        self.prio, self.ttl_ms, self.after_ms = opts
        self.text = text
        self.via = via


def parse_options(opts):
    """(prio, ttl in ms or None, after in ms) from the leading key=value
    options."""
    prio = opts.get("prio", "normal")
    if prio not in model.PRIORITY_RANK:
        raise CommandError("bad priority " + prio)
    ttl = None
    if "ttl" in opts:
        ttl = timefmt.parse_duration(opts["ttl"])
        if ttl <= 0:
            raise CommandError("bad ttl " + opts["ttl"])
    after = 0
    if "after" in opts:
        after = timefmt.parse_duration(opts["after"])
    return prio, ttl, after


def effective_ttl(svc, recipient, ttl_ms):
    """TTL of a new message: the requested one or the recipient's default,
    never more than the recipient's ``ttl.max_s``."""
    cfg = svc.cfg
    if ttl_ms is None:
        ttl_ms = cfg.ms("ttl.default_s", recipient)
    return min(ttl_ms, cfg.ms("ttl.max_s", recipient))


def has_room(svc, recipient):
    return svc.pending_for(recipient) < svc.cfg.get("queue.max_pending", recipient)


def submit(svc, req):
    """Run REQ through the acceptance checks.  Returns the Message or None."""
    if req.id in svc.messages:
        raise CommandError("message id %s already used" % req.id)
    svc.sender(req.sender)
    svc.recipient(req.recipient)
    if not req.text:
        raise CommandError("empty text")
    cfg = svc.cfg
    now = svc.now
    key = svc.dedup.key(req.sender, req.recipient, req.text)
    earlier = svc.dedup.check(key, now, cfg.ms("dedup.window_s", req.recipient), req.id)
    if earlier is not None:
        svc.stats.bump("duplicates")
        svc.event(now, "DUP %s of %s" % (req.id, earlier))
        return None
    if not has_room(svc, req.recipient):
        svc.stats.bump("rejected")
        svc.event(now, "REJECT %s queue-full" % req.id)
        return None
    msg = accept(svc, req, key)
    try_direct(svc, msg)
    return msg


def accept(svc, req, key):
    cfg = svc.cfg
    now = svc.now
    ttl = effective_ttl(svc, req.recipient, req.ttl_ms)
    svc.seq += 1
    frags = fragment.make_fragments(req.id, req.text, cfg.nbytes("frag.size_bytes"))
    msg = model.Message(req.id, req.sender, req.recipient, req.prio, req.text, svc.seq,
                        now, now + ttl, frags, req.via)
    msg.buffer = reassembly.Buffer(len(frags), msg.size)
    svc.messages[msg.id] = msg
    for frag in frags:
        frag.not_before = now + req.after_ms
        svc.queue.add(msg, frag)
    svc.stats.bump("accepted")
    invariant.check_capacity(svc, msg.recipient)
    text = "ACCEPT %s %s->%s prio=%s frags=%d size=%d ttl=%s" % (
        msg.id, msg.sender, msg.recipient, msg.prio, len(frags), msg.size,
        timefmt.fmt_seconds(ttl))
    if req.after_ms:
        text += " after=" + timefmt.fmt_seconds(req.after_ms)
    svc.note(msg, now, text)
    return msg


def try_direct(svc, msg):
    """Direct attempt (README, "Direct attempts"): an urgent message that
    fits in one fragment, to a recipient with nothing else pending and not
    paused, is attempted at once if the recipient's limits let it start."""
    if msg.prio != "urgent" or len(msg.frags) != 1 or msg.frags[0].not_before > svc.now:
        return False
    r = msg.recipient
    if svc.pending_for(r) != 1 or svc.breaker.paused(r):
        return False
    if svc.limits.block_reason(svc.cfg, r, svc.offset_of(r), svc.now, msg.size) is not None:
        return False
    entry = next(e for e in svc.queue.entries() if e.msg is msg)
    disp = svc.dispatcher
    outcome = disp.begin(entry, svc.now)
    disp.settle(entry, svc.now, outcome, direct=True)
    return True
