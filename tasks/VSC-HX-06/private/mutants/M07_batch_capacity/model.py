# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Plain data records: senders, recipients, messages and fragments."""

PRIORITIES = ("urgent", "high", "normal", "low")
PRIORITY_RANK = {p: i for i, p in enumerate(PRIORITIES)}

PENDING = "pending"
DELIVERED = "delivered"
FAILED = "failed"
EXPIRED = "expired"
CANCELLED = "cancelled"
FINAL_STATES = (DELIVERED, FAILED, EXPIRED, CANCELLED)


class Sender:
    __slots__ = ("name", "plan", "created_at")

    def __init__(self, name, plan, created_at):
        self.name = name
        self.plan = plan
        self.created_at = created_at


class Recipient:
    __slots__ = ("name", "offset_min", "created_at", "inbox")

    def __init__(self, name, offset_min, created_at):
        self.name = name
        self.offset_min = offset_min
        self.created_at = created_at
        self.inbox = []          # delivered (message id, sender, body), in order


class Fragment:
    __slots__ = ("msg_id", "index", "data", "attempts", "acked", "not_before")

    def __init__(self, msg_id, index, data):
        self.msg_id = msg_id
        self.index = index        # 1-based
        self.data = data          # bytes
        self.attempts = 0
        self.acked = False
        self.not_before = 0

    def label(self, total):
        return "%d/%d" % (self.index, total)


class Message:
    __slots__ = ("id", "sender", "recipient", "prio", "body", "size", "seq",
                 "accepted_at", "deadline", "frags", "state", "received_at",
                 "finished_at", "via", "buffer", "history")

    def __init__(self, msg_id, sender, recipient, prio, body, seq, accepted_at,
                 deadline, frags, via):
        self.id = msg_id
        self.sender = sender
        self.recipient = recipient
        self.prio = prio
        self.body = body
        self.size = len(body.encode("utf-8"))
        self.seq = seq
        self.accepted_at = accepted_at
        self.deadline = deadline
        self.frags = frags
        self.state = PENDING
        self.received_at = None   # first fragment received by the recipient
        self.finished_at = None
        self.via = via
        self.buffer = None
        self.history = []         # (instant, event text) in order

    @property
    def pending(self):
        return self.state == PENDING

    @property
    def started(self):
        return self.received_at is not None

    def ttl_ms(self):
        return self.deadline - self.accepted_at

    def unacked(self):
        return [f for f in self.frags if not f.acked]
