# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Per-recipient circuit breaker (README, "Pauses").

Every failed attempt (fail, busy or lost acknowledgement) adds one to the
recipient's count of failures in a row; every acknowledged attempt resets
it to zero.  When the count reaches
``breaker.threshold`` the recipient is paused for ``breaker.pause_s`` and
the count starts again from zero.  A paused recipient gets no attempts;
the pause ends at the first dispatch round at or after its end.
"""


class Breaker:
    def __init__(self):
        self._fails = {}
        self._until = {}

    def failures(self, recipient):
        return self._fails.get(recipient, 0)

    def on_success(self, recipient):
        self._fails[recipient] = 0

    def on_failure(self, recipient, now, threshold, pause_ms):
        """Count a failure; returns the pause end if this starts a pause."""
        n = self._fails.get(recipient, 0) + 1
        if n >= threshold:
            self._fails[recipient] = 0
            self._until[recipient] = now + pause_ms
            return now + pause_ms
        self._fails[recipient] = n
        return None

    def paused(self, recipient):
        return recipient in self._until

    def paused_until(self, recipient):
        return self._until.get(recipient)

    def due(self, now):
        """Recipients whose pause has ended at NOW (removed), sorted."""
        done = sorted(r for r, until in self._until.items() if until <= now)
        for r in done:
            del self._until[r]
        return done

    def wakeups(self, now):
        return [u for u in self._until.values() if u > now]
