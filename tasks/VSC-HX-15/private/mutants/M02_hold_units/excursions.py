# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Finds runs of out-of-band readings."""
import units


class Excursion:
    def __init__(self, start, end, is_open, kinds, peak):
        self.start = start
        self.end = end
        self.is_open = is_open
        self.kind = "mixed" if len(kinds) > 1 else next(iter(kinds))
        self.peak = peak

    @property
    def duration(self):
        return (self.end - self.start) // units.SEC_MS


def deviation(temp, lo, hi):
    return temp - hi if temp > hi else lo - temp


def find(rs, lo, hi):
    found = []
    run = None
    for r in rs:
        if lo <= r.temp <= hi:
            if run is not None:
                found.append(Excursion(run["start"], r.ts, False, run["kinds"], run["peak"]))
                run = None
            continue
        kind = "high" if r.temp > hi else "low"
        if run is None:
            run = {"start": r.ts, "kinds": {kind}, "peak": r.temp,
                   "dev": deviation(r.temp, lo, hi)}
        else:
            run["kinds"].add(kind)
            dev = deviation(r.temp, lo, hi)
            if dev > run["dev"]:
                run["peak"], run["dev"] = r.temp, dev
    if run is not None:
        found.append(Excursion(run["start"], rs[-1].ts, True, run["kinds"], run["peak"]))
    return found
