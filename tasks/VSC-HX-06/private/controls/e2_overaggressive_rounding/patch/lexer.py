# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Splitting command lines into tokens, options and free text.

Blanks are spaces and TABs.  A token is a run of non-blank characters.
A trailing TEXT argument is the rest of the line after the preceding tokens,
with blanks trimmed at both ends; it may contain any character.
"""

import re

from errors import CommandError

BLANKS = " \t"

# Sender and recipient names.  Because of this rule names never contain
# blanks, '=' or quotes, so they are printed as they are everywhere.
NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{0,23}$")
# Message ids.
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,31}$")


class Line:
    """One command line with lazy access to its tokens and trailing text."""

    def __init__(self, raw, number):
        self.raw = raw
        self.number = number
        self._spans = None

    def _scan(self):
        spans = []
        i, n = 0, len(self.raw)
        while i < n:
            while i < n and self.raw[i] in BLANKS:
                i += 1
            if i >= n:
                break
            j = i
            while j < n and self.raw[j] not in BLANKS:
                j += 1
            spans.append((i, j))
            i = j
        self._spans = spans

    @property
    def tokens(self):
        if self._spans is None:
            self._scan()
        return [self.raw[a:b] for a, b in self._spans]

    def rest(self, count):
        """Text after the first COUNT tokens, blanks trimmed ('' if none)."""
        if self._spans is None:
            self._scan()
        if count >= len(self._spans):
            return ""
        return self.raw[self._spans[count][0]:].strip(BLANKS)

    def is_blank_or_comment(self):
        stripped = self.raw.strip(BLANKS)
        return stripped == "" or stripped.startswith("#")


def need(tokens, count, usage):
    if len(tokens) < count:
        raise CommandError("usage: " + usage)


def exact(tokens, count, usage):
    if len(tokens) != count:
        raise CommandError("usage: " + usage)


def name(tok, what):
    if not NAME_RE.match(tok):
        raise CommandError("bad %s name %s" % (what, tok))
    return tok


def msg_id(tok):
    if not ID_RE.match(tok):
        raise CommandError("bad message id " + tok)
    return tok


def integer(tok, what, lo=None, hi=None):
    if not tok.isdigit() or len(tok) > 9:
        raise CommandError("bad %s %s" % (what, tok))
    value = int(tok)
    if lo is not None and value < lo:
        raise CommandError("%s out of range %s" % (what, tok))
    if hi is not None and value > hi:
        raise CommandError("%s out of range %s" % (what, tok))
    return value


def leading_options(tokens, start, allowed):
    """Consume ``key=value`` tokens from START while KEY is in ALLOWED.

    Returns (options dict, index of the first token that is not such an
    option).  A repeated option is an error.
    """
    opts = {}
    i = start
    while i < len(tokens):
        tok = tokens[i]
        key, eq, value = tok.partition("=")
        if not eq or key not in allowed:
            break
        if key in opts:
            raise CommandError("repeated option " + key)
        if value == "":
            raise CommandError("empty option " + key)
        opts[key] = value
        i += 1
    return opts, i
