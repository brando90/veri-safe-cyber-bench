# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The service state shared by all commands, and the output channel."""

import audit
import billing
import config
import dedup
import health
import limits
import link
import queueing
import stats
import timefmt
from errors import CommandError


class Service:
    def __init__(self, write):
        self._write = write
        self.now = 0
        self.cfg = config.Config()
        self.senders = {}
        self.recipients = {}
        self.messages = {}         # id -> Message, in acceptance order
        self.seq = 0
        self.queue = queueing.FragmentQueue()
        self.dedup = dedup.Dedup()
        self.limits = limits.Ledger()
        self.breaker = health.Breaker()
        self.links = link.Links()
        self.billing = billing.Billing()
        self.stats = stats.Stats()
        self.audit = audit.Audit()
        self.dispatcher = None     # set by dispatch.Dispatcher

    # ------------------------------------------------------------ output
    def emit(self, text):
        self._write(text)

    def event(self, at, text):
        self._write("%s %s" % (timefmt.fmt_instant(at), text))

    def note(self, msg, at, text):
        """An event about MSG: printed and kept in the message history."""
        msg.history.append((at, text))
        self.event(at, text)

    # ------------------------------------------------------------ lookups
    def sender(self, name):
        s = self.senders.get(name)
        if s is None:
            raise CommandError("unknown sender " + name)
        return s

    def recipient(self, name):
        r = self.recipients.get(name)
        if r is None:
            raise CommandError("unknown recipient " + name)
        return r

    def message(self, msg_id):
        m = self.messages.get(msg_id)
        if m is None:
            raise CommandError("unknown message " + msg_id)
        return m

    def pending(self):
        return [m for m in self.messages.values() if m.pending]

    def pending_for(self, recipient):
        return sum(1 for m in self.messages.values() if m.pending and m.recipient == recipient)

    def offset_of(self, recipient):
        return self.recipients[recipient].offset_min
