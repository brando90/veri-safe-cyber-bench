# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Per-recipient delivery limits (README, "Limits").

A message *starts* when the recipient receives its first fragment.  Before
a message may start, the recipient's limits are checked against the
messages that already started:

* ``limit.daily``     - messages started on the recipient's current local day;
* ``limit.hourly``    - messages started in the rolling hour (timewin);
* ``limit.daily_kib`` - bytes of the messages started on the current local
                        day plus this message's size.

A value of 0 means no limit.  Fragments of a message that already started
are never held back by limits.
"""

import localtime
import timewin
import units


class Ledger:
    def __init__(self):
        self._starts = {}     # recipient -> list of (instant, size, local day)
        self._hourly = {}     # recipient -> timewin.Rolling

    def _rolling(self, recipient):
        r = self._hourly.get(recipient)
        if r is None:
            r = self._hourly[recipient] = timewin.Rolling(units.MS_PER_HOUR)
        return r

    def count_day(self, recipient, day):
        return sum(1 for _, _, d in self._starts.get(recipient, ()) if d == day)

    def volume_day(self, recipient, day):
        return sum(size for _, size, d in self._starts.get(recipient, ()) if d == day)

    def block_reason(self, cfg, recipient, offset_min, now, size):
        """Why a message of SIZE bytes may not start at NOW, or None."""
        day = localtime.local_day(now, offset_min)
        daily = cfg.get("limit.daily", recipient)
        if daily and self.count_day(recipient, day) >= daily:
            return "daily"
        hourly = cfg.get("limit.hourly", recipient)
        if hourly and self._rolling(recipient).count(now) >= hourly:
            return "hourly"
        cap = cfg.nbytes("limit.daily_kib", recipient)
        if cap and self.volume_day(recipient, day) + size > cap:
            return "volume"
        return None

    def record(self, recipient, offset_min, now, size):
        day = localtime.local_day(now, offset_min)
        self._starts.setdefault(recipient, []).append((now, size, day))
        self._rolling(recipient).add(now)

    def wakeups(self, recipient, now):
        return self._rolling(recipient).wakeups(now)

    def summary(self, recipient, offset_min, now):
        day = localtime.local_day(now, offset_min)
        return (self.count_day(recipient, day), self.volume_day(recipient, day),
                self._rolling(recipient).count(now))
