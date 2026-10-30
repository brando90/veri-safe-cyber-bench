# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Audit log of operator actions and of pauses.

Each entry is printed ``#N <instant> <action> key=value ...``.  Every value
written here is a validated name, id, configuration key, number or clock
time (lexer.NAME_RE, lexer.ID_RE, config.KEYS), none of which can contain
blanks or '=', so values are written as they are.
"""

import timefmt


class Audit:
    def __init__(self):
        self.entries = []

    def add(self, at, action, *pairs):
        detail = " ".join("%s=%s" % (k, v) for k, v in pairs)
        self.entries.append((at, action, detail))

    def lines(self, last=None):
        items = list(enumerate(self.entries, 1))
        if last is not None:
            items = items[-last:] if last else []
        out = []
        for n, (at, action, detail) in items:
            text = "#%d %s %s" % (n, timefmt.fmt_instant(at), action)
            if detail:
                text += " " + detail
            out.append(text)
        return out
