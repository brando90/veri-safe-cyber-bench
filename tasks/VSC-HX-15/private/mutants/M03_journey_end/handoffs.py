# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Custody handoffs with a two-digit signature."""
import textnorm
from errors import CmdError

MAX_PARTY = 30


def signature(party, ts):
    return (sum(party.encode("utf-8")) + ts // 1000) % 100


class Handoff:
    def __init__(self, ts, party):
        self.ts = ts
        self.party = party
        self.sig = signature(party, ts)


class Custody:
    def __init__(self):
        self.chains = {}

    def add(self, sid, ts, party):
        party = textnorm.clean_label(party)
        if not party:
            raise CmdError("empty party")
        if len(party) > MAX_PARTY:
            raise CmdError("party name too long")
        chain = self.chains.setdefault(sid, [])
        if chain and chain[-1].ts > ts:
            raise CmdError("handoff out of order")
        chain.append(Handoff(ts, party))
        return len(chain)

    def drop(self, sid):
        self.chains.pop(sid, None)

    def chain(self, sid):
        return self.chains.get(sid, [])

    def verify(self, sid, number, sig):
        chain = self.chain(sid)
        if number < 1 or number > len(chain):
            raise CmdError("no such handoff")
        return chain[number - 1].sig == sig
