# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Registries of sites (depots and stops) and of routes over them."""
import re

import textnorm
import tsvfmt
from errors import CmdError

CODE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{1,5}$")
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,15}$")
MAX_STOPS = 12


class Sites:
    def __init__(self):
        self.names = {}

    def add(self, code, name):
        if not CODE_RE.match(code):
            raise CmdError("bad site code")
        code = code.upper()
        if code in self.names:
            raise CmdError("duplicate site %s" % code)
        self.names[code] = textnorm.check_label(name)
        return code

    def lookup(self, code):
        key = code.upper()
        if key not in self.names:
            raise CmdError("no such site %s" % code)
        return key

    def name(self, code):
        return self.names[code]

    def export_lines(self):
        lines = ["begin export sites"]
        for code in sorted(self.names):
            lines.append(tsvfmt.erow(["site", code, self.names[code]]))
        lines.append("end export sites")
        return lines


class Routes:
    def __init__(self):
        self.items = {}

    def add(self, rid, codes, sites):
        if not ID_RE.match(rid):
            raise CmdError("bad route id")
        if rid in self.items:
            raise CmdError("duplicate route %s" % rid)
        if len(codes) < 2 or len(codes) > MAX_STOPS:
            raise CmdError("a route needs 2 to %d stops" % MAX_STOPS)
        self.items[rid] = [sites.lookup(c) for c in codes]

    def has(self, rid):
        return rid in self.items

    def stops(self, rid):
        if rid not in self.items:
            raise CmdError("no such route %s" % rid)
        return self.items[rid]

    def count(self, rid):
        return len(self.stops(rid))

    def stop_at(self, rid, index):
        stops = self.stops(rid)
        if index < 0 or index >= len(stops):
            raise CmdError("no such stop")
        return stops[index]
