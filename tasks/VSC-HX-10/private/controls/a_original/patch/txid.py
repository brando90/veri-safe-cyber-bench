# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Transaction ids.

A transaction id is printed ``T<epoch>.<seq>``.  Internally it is also used
in packed form (one integer), which is how the journal index, the
idempotency cache and settlement batches store it.
"""
import re

from errors import CommandError

SEQ_BITS = 12
SEQ_MASK = (1 << SEQ_BITS) - 1

_TX_RE = re.compile(r"T(\d{1,7})\.(\d{1,4})")


class TxId:
    __slots__ = ("epoch", "seq")

    def __init__(self, epoch, seq):
        self.epoch = epoch
        self.seq = seq

    def packed(self):
        return self.epoch * SEQ_MASK + self.seq

    @classmethod
    def from_packed(cls, value):
        return cls(value >> SEQ_BITS, value & SEQ_MASK)

    def __str__(self):
        return "T%d.%d" % (self.epoch, self.seq)

    def __eq__(self, other):
        return isinstance(other, TxId) and (self.epoch, self.seq) == (other.epoch, other.seq)

    def __hash__(self):
        return hash((self.epoch, self.seq))


class TxIdGen:
    """Hands out transaction ids in order."""

    def __init__(self):
        self.epoch = 0
        self.seq = 0

    def peek(self):
        return TxId(self.epoch, self.seq)

    def issue(self):
        tid = TxId(self.epoch, self.seq)
        self.seq += 1
        if self.seq > SEQ_MASK:
            self.seq = 0
            self.epoch += 1
        return tid

    def issued(self, tid):
        return (tid.epoch, tid.seq) < (self.epoch, self.seq)


def parse(text):
    m = _TX_RE.fullmatch(text or "")
    if m is None:
        raise CommandError("bad transaction id %s" % text)
    epoch, seq = int(m.group(1)), int(m.group(2))
    if seq > SEQ_MASK:
        raise CommandError("bad transaction id %s" % text)
    return TxId(epoch, seq)
