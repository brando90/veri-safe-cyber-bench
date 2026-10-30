# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Global settings changed with the set command."""
import units
from errors import CmdError

SPECS = {
    "hold": (10, 1, 10080),
    "keep": (0, 0, 525600),
    "gap": (0, 0, 86400),
    "cap": (600, 0, 100000),
    "slack": (15, 0, 1440),
    "spike": (0, 0, 1000),
}


class Config:
    def __init__(self):
        self.values = {key: spec[0] for key, spec in SPECS.items()}

    def set(self, key, text):
        if key not in SPECS:
            raise CmdError("unknown setting %s" % key)
        _default, lo, hi = SPECS[key]
        self.values[key] = units.parse_int(text, key, lo, hi)
        return self.values[key]

    def get(self, key):
        return self.values[key]

    def duration_ms(self, key):
        return self.values[key] * units.MIN_MS

    def gap_ms(self):
        return self.values["gap"] * units.SEC_MS

    def keep_ms(self):
        minutes = self.values["keep"]
        return None if minutes == 0 else minutes * units.MIN_MS

    def line(self):
        return "config " + " ".join("%s=%d" % (k, self.values[k]) for k in SPECS)


BANDS = {
    "frozen": (-250, -150),
    "chilled": (20, 80),
    "cool": (80, 150),
    "ambient": (150, 250),
    "vaccine": (20, 80),
}


def band(name):
    if name not in BANDS:
        raise CmdError("unknown class %s" % name)
    return BANDS[name]


def listing():
    lines = []
    for name in sorted(BANDS):
        lo, hi = BANDS[name]
        lines.append("profile %s %s..%s" % (name, units.fmt_tenths(lo), units.fmt_tenths(hi)))
    return lines
