# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Duplicate detection.

A message is a duplicate when the same sender sent the same body to the
same recipient, and that earlier message was accepted inside the
recipient's ``dedup.window_s`` window (timewin.within).  Only accepted
messages are remembered.  A duplicate does not restart the window: the
window always runs from the remembered acceptance.
"""

import timewin


class Dedup:
    def __init__(self):
        self._seen = {}   # (sender, recipient, body) -> (accepted_at, msg_id)

    @staticmethod
    def key(sender, recipient, body):
        return (sender, recipient, body)

    def find(self, key, now, window_ms):
        """Id of the remembered message KEY duplicates at NOW, or None."""
        entry = self._seen.get(key)
        if entry is None:
            return None
        accepted_at, msg_id = entry
        if timewin.within(accepted_at, now, window_ms) and now - accepted_at != window_ms:
            return msg_id
        return None

    def remember(self, key, now, msg_id):
        self._seen[key] = (now, msg_id)

    def check(self, key, now, window_ms, msg_id):
        """find() and, when it is not a duplicate, remember() in one step.
        Used by the v1 spool replay (legacy.py)."""
        earlier = self.find(key, now, window_ms)
        if earlier is None:
            self.remember(key, now, msg_id)
        return earlier

    def size(self):
        return len(self._seen)
