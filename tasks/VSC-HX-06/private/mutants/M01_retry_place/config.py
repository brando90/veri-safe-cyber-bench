# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Layered configuration.

Three layers, later wins: built-in defaults, global overrides (``set``),
per-recipient overrides (``set-for``).  Only keys whose scope is
"recipient" can be overridden per recipient.

Every key has a unit, visible in its name (``_ms``, ``_s``, ``_kib``,
``_bytes``) or listed in KEYS.  ``get`` returns the stored number in the
key's own unit; ``ms`` and ``nbytes`` return it converted to milliseconds
or bytes, which is what the engine works in.
"""

import units
import timefmt
from errors import CommandError


class Key:
    __slots__ = ("unit", "scope", "default", "lo", "hi", "doc")

    def __init__(self, unit, scope, default, lo, hi, doc):
        self.unit = unit
        self.scope = scope
        self.default = default
        self.lo = lo
        self.hi = hi
        self.doc = doc


KEYS = {
    "dispatch.interval_ms": Key("ms", "global", 1000, 100, 60000,
                                "time between dispatch rounds"),
    "dispatch.batch": Key("count", "global", 4, 1, 100,
                          "attempts per dispatch round"),
    "dispatch.per_recipient": Key("count", "recipient", 1, 1, 100,
                                  "attempts per recipient per round"),
    "frag.size_bytes": Key("bytes", "global", 32, 4, 65536,
                           "largest fragment"),
    "retry.base_ms": Key("ms", "global", 2000, 1, 600000,
                         "delay after the first failed attempt"),
    "retry.factor": Key("count", "global", 2, 1, 10,
                        "delay multiplier per further failure"),
    "retry.cap_s": Key("s", "global", 60, 1, 86400,
                       "longest backoff delay"),
    "retry.max_attempts": Key("count", "recipient", 4, 1, 10,
                              "attempts per fragment"),
    "dedup.window_s": Key("s", "recipient", 300, 0, 86400,
                          "duplicate detection window"),
    "ttl.default_s": Key("s", "recipient", 3600, 1, 604800,
                         "TTL when send gives none"),
    "ttl.max_s": Key("s", "recipient", 86400, 1, 604800,
                     "longest TTL"),
    "queue.max_pending": Key("count", "recipient", 50, 1, 10000,
                             "pending messages per recipient"),
    "limit.daily": Key("count", "recipient", 0, 0, 100000,
                       "messages started per local day (0 = no limit)"),
    "limit.hourly": Key("count", "recipient", 0, 0, 100000,
                        "messages started per rolling hour (0 = no limit)"),
    "limit.daily_kib": Key("kib", "recipient", 0, 0, 1048576,
                           "volume started per local day (0 = no limit)"),
    "quiet.start": Key("hhmm", "recipient", None, None, None,
                       "start of quiet hours, local time"),
    "quiet.end": Key("hhmm", "recipient", None, None, None,
                     "end of quiet hours, local time"),
    "breaker.threshold": Key("count", "recipient", 3, 1, 100,
                             "failures in a row before a pause"),
    "breaker.pause_s": Key("s", "recipient", 30, 1, 86400,
                           "length of a pause"),
}


class Config:
    def __init__(self):
        self._global = {}
        self._per = {}          # recipient -> {key: value}
        self.version = 0

    # ------------------------------------------------------------ reading
    def get(self, key, recipient=None):
        """Value of KEY in its own unit, for RECIPIENT if given."""
        spec = KEYS[key]
        if recipient is not None and spec.scope == "recipient":
            layer = self._per.get(recipient)
            if layer is not None and key in layer:
                return layer[key]
        if key in self._global:
            return self._global[key]
        return spec.default

    def source(self, key, recipient=None):
        spec = KEYS[key]
        if recipient is not None and spec.scope == "recipient":
            if key in self._per.get(recipient, {}):
                return "recipient"
        if key in self._global:
            return "global"
        return "default"

    def ms(self, key, recipient=None):
        """Value of a time key in milliseconds."""
        spec = KEYS[key]
        return self.get(key, recipient) * units.TIME_SCALE[spec.unit]

    def nbytes(self, key, recipient=None):
        """Value of a size key in bytes."""
        spec = KEYS[key]
        return self.get(key, recipient) * units.SIZE_SCALE[spec.unit]

    def quiet(self, recipient):
        """(start, end) minutes of the day, or None when not configured or
        when start equals end (an empty window)."""
        start = self.get("quiet.start", recipient)
        end = self.get("quiet.end", recipient)
        if start is None or end is None or start == end:
            return None
        return start, end

    # ------------------------------------------------------------ writing
    def parse_value(self, key, text):
        spec = KEYS.get(key)
        if spec is None:
            raise CommandError("unknown key " + key)
        if spec.unit == "hhmm":
            if text == "-":
                return None
            return timefmt.parse_hhmm(text)
        if not text.isdigit() or len(text) > 9:
            raise CommandError("bad value %s for %s" % (text, key))
        value = int(text)
        if value < spec.lo or value > spec.hi:
            raise CommandError("value %s out of range for %s (%d..%d)"
                               % (text, key, spec.lo, spec.hi))
        return value

    def set_global(self, key, value):
        self._global[key] = value
        self.version += 1

    def set_for(self, recipient, key, value):
        if KEYS[key].scope != "recipient":
            raise CommandError("key %s cannot be set per recipient" % key)
        self._per.setdefault(recipient, {})[key] = value
        self.version += 1

    def clear_for(self, recipient, key):
        layer = self._per.get(recipient, {})
        if key not in layer:
            raise CommandError("no override of %s for %s" % (key, recipient))
        del layer[key]
        self.version += 1

    # ------------------------------------------------------------ listing
    def rows(self, recipient=None):
        out = []
        for key in sorted(KEYS):
            spec = KEYS[key]
            if recipient is not None and spec.scope != "recipient":
                continue
            value = self.get(key, recipient)
            out.append((key, render(spec, value), self.source(key, recipient)))
        return out


def render(spec, value):
    if spec.unit == "hhmm":
        return "-" if value is None else timefmt.fmt_hhmm(value)
    return str(value)
