# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""A priority queue of due items.

Order: earlier due time first, then higher priority, then lower sequence
number.  ``push`` hands out a fresh sequence number unless one is given, so
callers that put an item back can keep its original place among equals.
"""
import heapq


class PQueue:
    def __init__(self):
        self._heap = []
        self._next = 1
        self._cancelled = set()

    def next_seq(self):
        seq = self._next
        self._next += 1
        return seq

    def push(self, item, due, prio, seq=None):
        if seq is None:
            seq = self.next_seq()
        heapq.heappush(self._heap, (due, -prio, seq, item.id, item))
        return seq

    def pop_due(self, now):
        """Remove and return, in order, every item due at or before NOW."""
        out = []
        while self._heap and self._heap[0][0] <= now:
            entry = heapq.heappop(self._heap)
            if entry[3] in self._cancelled:
                self._cancelled.discard(entry[3])
                continue
            out.append(entry[4])
        return out

    def cancel(self, item_id):
        if any(e[3] == item_id for e in self._heap) and item_id not in self._cancelled:
            self._cancelled.add(item_id)
            return True
        return False

    def ordered(self):
        return [e[4] for e in sorted(self._heap) if e[3] not in self._cancelled]

    def __len__(self):
        return len(self._heap) - len(self._cancelled)
