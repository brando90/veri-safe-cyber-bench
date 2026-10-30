# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The dispatch queue: one entry per fragment that still has to be attempted.

Order (README, "Dispatch order"), smallest key first:

1. priority (urgent, high, normal, low);
2. sender turn: the sender whose latest attempt is the oldest goes first;
   senders without any attempt yet go before all others;
3. queue order: the order in which entries joined the queue (a message's
   fragments join together when it is accepted);
4. fragment number.

An entry stays in the queue until its fragment is acknowledged or its
message reaches a final state.
"""

import model


class Entry:
    __slots__ = ("msg", "frag", "order")

    def __init__(self, msg, frag, order):
        self.msg = msg
        self.frag = frag
        self.order = order


class FragmentQueue:
    def __init__(self):
        self._entries = []
        self._next_order = 0
        self._services = 0
        self._turn = {}       # sender -> number of its latest attempt
        self._last_at = {}    # sender -> instant of its latest attempt

    def __len__(self):
        return len(self._entries)

    # ------------------------------------------------------------ membership
    def add(self, msg, frag):
        """Append a new entry for FRAG at the end of the queue order."""
        self._next_order += 1
        entry = Entry(msg, frag, self._next_order)
        self._entries.append(entry)
        return entry

    def take(self, entry):
        self._entries.remove(entry)

    def drop_message(self, msg_id):
        self._entries = [e for e in self._entries if e.msg.id != msg_id]

    def entries(self):
        return list(self._entries)

    # ------------------------------------------------------------ ordering
    def turn_of(self, sender):
        return self._turn.get(sender, -1)

    def sort_key(self, entry):
        msg = entry.msg
        return (model.PRIORITY_RANK[msg.prio], self.turn_of(msg.sender),
                entry.order, entry.frag.index)

    def best(self, eligible):
        """The eligible entry with the smallest key, or None."""
        best, best_key = None, None
        for entry in self._entries:
            if not eligible(entry):
                continue
            key = self.sort_key(entry)
            if best is None or key < best_key:
                best, best_key = entry, key
        return best

    def ordered(self):
        return sorted(self._entries, key=self.sort_key)

    def mark_served(self, sender, now):
        """Record an attempt for SENDER at instant NOW."""
        self._services += 1
        self._turn[sender] = now
        self._last_at[sender] = now

    def last_served_at(self, sender):
        return self._last_at.get(sender)

    def services(self):
        return self._services
