# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The account slot table.

Every open account occupies one of a fixed number of slots.  A slot number
together with the slot's generation identifies an account for its whole
life; the generation of a slot goes up each time the slot is handed out
again.  Callables in ``recycle_hooks`` are called with the slot number when
a slot is handed out again.
"""
from collections import deque

from errors import CommandError


class SlotTable:
    def __init__(self, size):
        self.size = size
        self.fresh = 0
        self.free = deque()
        self.gen = [0] * size
        self.busy = [False] * size
        self.recycle_hooks = []

    def take(self):
        if self.free and min(self.free) < self.fresh:
            idx = min(self.free)
            self.free.remove(idx)
            self.gen[idx] += 1
            for hook in self.recycle_hooks:
                hook(idx)
            self.busy[idx] = True
            return idx, self.gen[idx]
        if self.fresh < self.size:
            idx = self.fresh
            self.fresh += 1
        elif self.free:
            idx = self.free.popleft()
            self.gen[idx] += 1
            for hook in self.recycle_hooks:
                hook(idx)
        else:
            raise CommandError("no free slot")
        self.busy[idx] = True
        return idx, self.gen[idx]

    def give_back(self, idx):
        if not self.busy[idx]:
            raise CommandError("slot %d is not in use" % idx)
        self.busy[idx] = False
        self.free.append(idx)

    def in_use(self):
        return sum(1 for b in self.busy if b)
