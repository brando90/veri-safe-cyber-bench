# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Simulated links to recipients.

Every attempt to a recipient takes the next scripted outcome for that
recipient (``link`` command), or "ok" when nothing is scripted:

* ok    - the recipient received the fragment and acknowledged it;
* fail  - the fragment did not arrive;
* busy  - the fragment did not arrive; the recipient asks the sender to
          wait at least AFTER seconds before the next attempt;
* lost  - the fragment arrived but the acknowledgement was lost, so the
          sender sees a failure.
"""

from collections import deque

OK = "ok"
FAIL = "fail"
BUSY = "busy"
LOST = "lost"
KINDS = (OK, FAIL, BUSY, LOST)


class Outcome:
    __slots__ = ("kind", "after_s")

    def __init__(self, kind, after_s=0):
        self.kind = kind
        self.after_s = after_s      # busy only: retry-after hint, seconds

    @property
    def arrived(self):
        return self.kind in (OK, LOST)

    @property
    def acked(self):
        return self.kind == OK

    def word(self):
        return {OK: "ok", FAIL: "fail", BUSY: "busy", LOST: "lost-ack"}[self.kind]


_DEFAULT = Outcome(OK)


class Links:
    def __init__(self):
        self._script = {}

    def script(self, recipient, kind, count, after_s=0):
        q = self._script.setdefault(recipient, deque())
        for _ in range(count):
            q.append(Outcome(kind, after_s))

    def clear(self, recipient):
        self._script.pop(recipient, None)

    def next(self, recipient):
        q = self._script.get(recipient)
        if q:
            return q.popleft()
        return _DEFAULT

    def queued(self, recipient):
        return len(self._script.get(recipient, ()))
